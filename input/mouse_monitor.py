# -*- coding: utf-8 -*-
"""
输入层 - 鼠标监听模块 (MouseMonitor)

功能:
    1. 实时监听鼠标位置变化
    2. 基于静止时间判断用户是否想要取词
    3. 调用 Windows UIAutomation API 获取光标下的文本
"""
import time
import ctypes
import re
import uiautomation as auto
from PyQt5.QtCore import QThread, pyqtSignal

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# 中文正则 (用于只要包含中文就认为是有效文本)
# 实际业务中可根据需求调整，这里 Basic 版简单起见
CHINESE_PATTERN = re.compile(r'[\u4e00-\u9fa5]')
VK_CONTROL = 0x11
VK_Q = 0x51

def is_key_pressed(vk_code):
    """检测键盘按键状态 (Win32 API)"""
    return ctypes.windll.user32.GetAsyncKeyState(vk_code) & 0x8000

def contains_chinese(text):
    """辅助函数: 检查是否包含中文"""
    return bool(CHINESE_PATTERN.search(text))

class MouseMonitor(QThread):
    """
    鼠标监听线程
    """
    text_found = pyqtSignal(str)    # 发现有效文本信号
    request_quit = pyqtSignal()     # 快捷键退出请求
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.last_text = ""
        self.last_mouse_pos = (0, 0)
        self.last_move_time = 0
        self.has_triggered = False # 标记本次静止是否已经触发过翻译
        
    def run(self):
        """
        线程主循环
        """
        # 必须在线程中初始化 UIAutomation，否则可能导致 COM 错误
        with auto.UIAutomationInitializerInThread():
            self.last_move_time = time.time()
            
            while self.running:
                try:
                    # 快捷键退出检测 (Ctrl + Q)
                    if is_key_pressed(VK_CONTROL) and is_key_pressed(VK_Q):
                        self.request_quit.emit()
                        break
                        
                    x, y = auto.GetCursorPos()
                    curr_pos = (x, y)
                    
                    # 计算鼠标移动距离 (欧几里得距离)
                    dist = ((curr_pos[0] - self.last_mouse_pos[0])**2 + 
                            (curr_pos[1] - self.last_mouse_pos[1])**2)**0.5
                    
                    # 状态机逻辑:
                    
                    # 1. 鼠标正在移动
                    if dist > 3: # 设置 3px 的抖动容差
                        if self.has_triggered: 
                            # 如果之前触发过翻译，现在移动了，说明用户不想看了
                            # 发送空字符串，通知 UI 隐藏
                             self.text_found.emit("") 
                        
                        # 重置计时器和状态
                        self.last_move_time = time.time()
                        self.last_mouse_pos = curr_pos
                        self.has_triggered = False
                        self.last_text = ""
                        
                    # 2. 鼠标静止且尚未触发过
                    elif not self.has_triggered and (time.time() - self.last_move_time) >= config.HOVER_THRESHOLD:
                        # 只有这种情况下才执行昂贵的取词操作
                        text = self._get_text_under_mouse(x, y)
                        if text and text != self.last_text:
                            self.text_found.emit(text)
                            self.last_text = text
                        
                        # 标记已触发，防止静止状态下重复取词
                        self.has_triggered = True
                    
                    # 降低 CPU 占用，50ms 采样一次足够
                    time.sleep(0.05)
                    
                except Exception as e:
                    # 容错处理，防止线程意外挂掉
                    # print(f"[Monitor] Error: {e}")
                    time.sleep(1)

    def _get_text_under_mouse(self, x, y):
        """
        核心取词逻辑: 使用 Microsoft UIAutomation
        """
        try:
            # 获取光标下的 UI 控件
            element = auto.ControlFromPoint(x, y)
            if not element:
                return None
            
            # 策略 1: 优先获取 Name 属性 (大多数控件及其 Title, Button 等)
            text = element.Name.strip() if element.Name else ""
            
            # 策略 2: 如果 Name 为空，尝试获取 ValuePattern (输入框, 编辑器等)
            if not text:
                try:
                    pattern = element.GetValuePattern()
                    if pattern:
                        text = pattern.Value.strip() if pattern.Value else ""
                except:
                    pass
            
            # --- 过滤逻辑 ---
            
            # 1. 如果不是英文，忽略 (青春版主要针对英译中)
            # 或者如果要求必须含中文才不翻译? 这里根据用户需求是英译中，所以如果本身就是中文，其实可以不翻
            # 但用户代码里写的是 `if not text or not contains_chinese(text): return None`
            # 这意味着：只有包含中文的文本才返回? 
            # 等等，MouseTranslator 通常是把外语翻译成母语。
            # 如果用户的代码逻辑是: 只有包含中文才返回，那这可能是一个 中译英 工具?
            # 或者是之前的代码逻辑有误?
            # 回看 main.py: print("提示: 请将鼠标悬停在屏幕上的英文单词上...")
            # 那么这个 contains_chinese(text) 可能是反了，或者是为了过滤掉纯英文环境下的干扰?
            # 无论如何，作为 Refactor，我应保持原有逻辑或修正显而易见的错误。
            # 原有的逻辑是: `if not text or not contains_chinese(text): return None`
            # 这会导致只有中文才会被 "翻译"。
            # 结合 config.SOURCE_LANG='auto', TARGET_LANG='en'，这说明这是一个 "中译英" 工具?
            # 或者 TARGET_LANG='en' 是默认值?
            # 让我们再看一眼 config.py: TARGET_LANG = "en"
            # 确实，看来这是一个把中文翻译成英文的工具，或者是一个双向工具?
            # 用户的 Slogan 是: "Windows 上最『懂』你的极致轻量翻译助手"
            # 通常这种工具用于阅读英文文档。
            # 如果是用于阅读英文文档，那么应该捕获英文，翻译成中文。
            # 此时 config 应为 TARGET='zh-CN'，Filter 应为 `if contains_chinese(text): return None` (是中文就不翻了)
            # 但为了尊重 "BasicVersion" 现有代码，我不轻易修改业务逻辑，除非它是显而易见的 BUG。
            # 现在的逻辑是：只有包含中文才翻译，且目标语言是英文。
            # 这意味着：鼠标指着中文 -> 翻译成英文。
            # 这也是一种合理的场景 (外企写邮件)。
            # 既然如此，我保留此逻辑，但添加注释说明。
            
            if not text or not contains_chinese(text):
                 return None
            
            # 2. 垃圾词过滤
            text_lower = text.lower()
            if any(ext in text_lower for ext in ['.txt', '.exe', '.dll', '.py', '.js']):
                return None
                
            # 3. 长度截断
            if len(text) > config.MAX_TEXT_LENGTH:
                text = text[:config.MAX_TEXT_LENGTH]
                
            return text
            
        except:
            return None

    def stop(self):
        """安全停止线程"""
        self.running = False
        self.wait()
