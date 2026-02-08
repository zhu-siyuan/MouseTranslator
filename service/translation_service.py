# -*- coding: utf-8 -*-
"""
服务层 - 翻译服务 (TranslationService)

特点:
    1. 极致轻量: 并未引入复杂的 requests 封装，直接使用 deep-translator
    2. 无状态: 不使用缓存 (Redis/SQLite)，减少磁盘 IO 和依赖
    3. 异步: 使用线程池避免阻塞 UI 主线程
"""
from deep_translator import GoogleTranslator
from PyQt5.QtCore import QObject, pyqtSignal
import threading

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class TranslationService(QObject):
    """
    提供基础翻译能力的服务类
    """
    # 定义 Qt 信号，用于在翻译完成时通知 UI 线程
    translation_finished = pyqtSignal(str, str) # 参数: 原文, 译文
    translation_error = pyqtSignal(str, str)    # 参数: 原文, 错误信息

    def __init__(self):
        super().__init__()
        # 初始化 Google 翻译引擎
        # source='auto' 让 Google 自动检测语言
        self.translator = GoogleTranslator(source=config.SOURCE_LANG, target=config.TARGET_LANG)

    def translate(self, text):
        """
        执行翻译任务 (非阻塞)
        
        Args:
            text (str): 待翻译的文本
        """
        if not text:
            return
            
        print(f"[Translation] 开始翻译: {text[:20]}...")
        # 启动后台线程执行网络请求，防止界面卡顿
        threading.Thread(target=self._do_translate, args=(text,), daemon=True).start()

    def _do_translate(self, text):
        """
        后台线程执行的具体逻辑
        """
        try:
            # 调用 deep_translator 进行网络请求
            # 注意: 这里受网络环境影响较大
            result = self.translator.translate(text)
            
            if result:
                # 发射信号，将结果传回主线程
                self.translation_finished.emit(text, result)
            else:
                self.translation_error.emit(text, "无结果")
                
        except Exception as e:
            # 捕获网络异常 (如超时、DNS 解析失败)
            print(f"[Translation] 翻译出错: {e}")
            self.translation_error.emit(text, "网络超时")
