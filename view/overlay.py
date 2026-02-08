# -*- coding: utf-8 -*-
"""
视图层 - 悬浮窗模块 (Overlay)

功能:
    1. 显示原文和翻译结果
    2. 自动跟随鼠标位置
    3. 智能边缘检测，防止超出屏幕
    4. 鼠标穿透 (TransparentForMouseEvents)，不影响用户正常操作下层窗口
"""
import sys
import os
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# 极简暗色主题样式 (Dark Mode)
STYLE_NORMAL = """
    QLabel {
        background-color: #1e1e1e;   /* 深灰背景 */
        color: #ffffff;              /* 白色文字 */
        border: 1px solid #333333;   /* 微妙的边框 */
        border-radius: 4px;          /* 圆角 */
        padding: 6px;                /* 内边距 */
        font-family: "Microsoft YaHei", sans-serif;
        font-size: 13px;
    }
"""

class Overlay(QWidget):
    """
    无边框悬浮窗控件
    """
    def __init__(self):
        super().__init__()
        self._init_ui()
        
    def _init_ui(self):
        """
        初始化窗口属性
        """
        # FramelessWindowHint: 无边框
        # WindowStaysOnTopHint: 总是置顶
        # Tool: 工具窗口 (不在任务栏显示)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        
        # TransparentForMouseEvents: 鼠标穿透的关键
        # 即使悬浮窗盖住了按钮，用户点击悬浮窗时，事件会穿透到下层按钮
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        
        self.label = QLabel("")
        self.label.setStyleSheet(STYLE_NORMAL)
        self.label.setWordWrap(True) # 自动换行
        self.label.setMaximumWidth(350) # 限制最大宽度，防止太宽遮挡视线
        
        self.layout.addWidget(self.label)
        self.hide() # 初始隐藏

    def update_content(self, original_text, translation=None, is_translating=False, error=False):
        """
        更新显示内容
        """
        if not original_text:
            self.hide()
            return
        
        content = ""
        if is_translating:
            content = f"{original_text}\n\n[正在翻译...]"
        elif error:
            content = f"{original_text}\n\n[翻译失败]"
        elif translation:
            content = f"{original_text}\n\n{translation}"
        else:
            self.hide()
            return
            
        self.label.setText(content)
        self.label.adjustSize()
        self.adjustSize()
        self.show()

    def update_position(self, x, y):
        """
        智能更新位置: 确保悬浮窗始终在屏幕可见范围内，且不遮挡鼠标
        
        Args:
            x (int): 鼠标 X 坐标
            y (int): 鼠标 Y 坐标
        """
        try:
            # 基础位置: 鼠标右下角
            offset = 20 # 稍微加大间距，防止遮挡鼠标，确保用户能看清鼠标所指
            target_x = int(x) + offset
            target_y = int(y) + offset
            
            # 获取当前屏幕几何信息 (多屏支持)
            screen = None
            if hasattr(self, 'screen') and self.screen():
                screen = self.screen().geometry()
            else:
                from PyQt5.QtWidgets import QApplication
                screen = QApplication.primaryScreen().geometry()
                
            if screen:
                # 边缘碰撞检测
                
                # 1. 右边界处理: 如果超出屏幕右侧，移到鼠标左侧
                if target_x + self.width() > screen.right():
                    target_x = int(x) - self.width() - offset
                
                # 2. 下边界处理: 如果超出屏幕底部，移到鼠标上方
                if target_y + self.height() > screen.bottom():
                    target_y = int(y) - self.height() - offset
                
                # 3. 左/上边界兜底 (防止移出屏幕左上角)
                # 这种情况较少见，通常发生在屏幕分辨率变更时
                target_x = max(screen.left(), target_x)
                target_y = max(screen.top(), target_y)
            
            self.move(target_x, target_y)
            self.raise_() # 确保在 Z 轴最上层
            
        except Exception as e:
            print(f"[Overlay] Position Error: {e}")
