# -*- coding: utf-8 -*-
"""
控制器层 - 主控制器 (MainController)

功能:
    作为 MVC 架构的核心调度器，负责协调:
    1. Input 层 (MouseMonitor) 的信号输入
    2. Service 层 (TranslationService) 的业务处理
    3. View 层 (Overlay) 的界面更新
    
    实现 "监听 -> 捕获 -> 显示(占位) -> 翻译 -> 更新显示" 的完整链路。
"""
import sys
from PyQt5.QtCore import QObject, pyqtSlot, QTimer

from input.mouse_monitor import MouseMonitor
from service.translation_service import TranslationService
from view.overlay import Overlay
import config

class MainController(QObject):
    """
    主控制器类
    """
    def __init__(self):
        super().__init__()
        
        # 1. 初始化各层组件
        self.monitor = MouseMonitor()
        self.service = TranslationService()
        self.overlay = Overlay()
        
        # 2. 连接组件间的信号与槽
        self._connect_signals()
        
    def start(self):
        """
        启动系统流程
        """
        print("[Controller] 正在启动 MouseMonitor (鼠标监听模块)...")
        self.monitor.start()
        
    def stop(self):
        """
        停止系统 (通常由操作系统或托盘退出触发)
        """
        self.monitor.stop()
        
    def _connect_signals(self):
        """
        定义信号路由规则
        """
        # Input -> Controller
        self.monitor.text_found.connect(self._on_text_found)
        self.monitor.request_quit.connect(sys.exit)
        
        # Service -> Controller
        self.service.translation_finished.connect(self._on_translation_finished)
        self.service.translation_error.connect(self._on_translation_error)
        
    @pyqtSlot(str)
    def _on_text_found(self, text):
        """
        处理 Input 层捕获到的文本
        """
        if not text:
            # 如果文本为空（例如鼠标移开），隐藏悬浮窗
            self.overlay.hide()
            return
            
        print(f"[Controller] 捕获文本: {text[:10]}...")
        
        # 1. 立即响应: 更新 UI 显示原文，并标记 "正在翻译..."
        # 这一步是为了给用户即时反馈，避免网络请求造成的视觉延迟
        self.overlay.update_content(text, is_translating=True)
        
        # 2. 动态定位: 根据当前鼠标位置和 UI 大小计算最佳显示坐标
        from PyQt5.QtGui import QCursor
        curr_pos = QCursor.pos()
        self.overlay.update_position(curr_pos.x(), curr_pos.y())
        self.overlay.show() # 强制显示
        
        # 3. 异步请求: 调用后台服务进行翻译
        self.service.translate(text)
        
    @pyqtSlot(str, str)
    def _on_translation_finished(self, original, translation):
        """
        处理翻译成功的可以直接回调
        """
        # 只有当悬浮窗当前仍对应原来的文本时才更新
        # 防止用户快速移动导致之前的请求覆盖了新的显示
        if self.overlay.isVisible():
            self.overlay.update_content(original, translation=translation)
            
            # 翻译结果可能比原文长或短，导致窗体尺寸变化
            # 需要再次校准位置，防止内容超出屏幕边界
            from PyQt5.QtGui import QCursor
            curr_pos = QCursor.pos()
            self.overlay.update_position(curr_pos.x(), curr_pos.y())
             
    @pyqtSlot(str, str)
    def _on_translation_error(self, original, error_msg):
        """
        处理翻译失败的回调
        """
        if self.overlay.isVisible():
            self.overlay.update_content(original, error=True)
