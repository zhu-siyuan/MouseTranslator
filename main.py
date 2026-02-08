# -*- coding: utf-8 -*-
"""
MouseTranslator BasicVersion Entry Point (程序入口)

功能:
    1. 初始化 PyQt5 应用程序
    2. 设置 DPI 适配 (High DPI Scaling)
    3. 启动 MVC 架构的主控制器
    4. 创建系统托盘图标
"""
import sys
import os
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QCoreApplication

# 设置 DPI 自适应 (适配 4K/2K 高分屏)
# 必须在创建 QApplication 之前设置
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
QCoreApplication.setAttribute(5) # Qt.AA_UseHighDpiPixmaps

import config
from controller.main_controller import MainController

def main():
    """
    主函数：程序生命周期管理
    """
    # 单例检查 (简化版)
    # 商业版此处会包含互斥锁 (Mutex) 防止多开，青春版假设用户自觉
    
    app = QApplication(sys.argv)
    
    # 设置为 False，确保关闭所有窗口后程序不退出 (因为我们要常驻托盘)
    app.setQuitOnLastWindowClosed(False)
    
    # 初始化控制器 (核心业务逻辑)
    controller = MainController()
    controller.start()
    
    # --- 系统托盘设置 ---
    tray = QSystemTrayIcon()
    if os.path.exists(config.ICON_PATH):
        tray.setIcon(QIcon(config.ICON_PATH))
    else:
        # 如果没有图标，可以考虑生成一个临时的或留空
        pass
        
    menu = QMenu()
    
    # 状态显示 (仅展示当前版本信息，不可点击)
    status_action = QAction(f"{config.APP_NAME} 青春版", menu)
    status_action.setEnabled(False) # 变灰显示
    menu.addAction(status_action)
    
    menu.addSeparator()
    
    # 退出按钮
    quit_action = QAction("退出程序", menu)
    quit_action.triggered.connect(app.quit)
    menu.addAction(quit_action)
    
    tray.setContextMenu(menu)
    tray.show()
    
    print(f"[{config.APP_NAME}] 启动成功 (BasicVersion)")
    print("提示: 请将鼠标悬停在屏幕上的英文单词上...")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
