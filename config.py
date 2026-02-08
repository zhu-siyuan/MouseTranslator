# -*- coding: utf-8 -*-
"""
MouseTranslator BasicVersion 配置文件
定义全局常量、路径和参数。
"""
import sys
import os

# ========== 翻译引擎配置 ==========
# 青春版使用单源 Google 翻译，无备用引擎
API_TIMEOUT = 5.0          # API 请求超时时间 (秒)
GOOGLE_TEST_URL = "https://translate.googleapis.com"
PROXY_URL = ""             # 代理地址 (例如: "http://127.0.0.1:7890")，留空则不使用

# ========== 应用路径 ==========
APP_NAME = "MouseTranslator"

# 自动判断运行环境 (源代码 vs 打包后的 .exe)
if getattr(sys, 'frozen', False):
    BASE_PATH = os.path.dirname(sys.executable)
else:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

ICON_PATH = os.path.join(BASE_PATH, "icon.png")

# ========== 交互参数 ==========
HOVER_THRESHOLD = 0.5      # 鼠标悬停触发翻译的时间阈值 (0.5秒)
OFFSET_X = 15              # 悬浮窗距离鼠标的水平偏移量 (像素)
OFFSET_Y = 15              # 悬浮窗距离鼠标的垂直偏移量 (像素)
MAX_TEXT_LENGTH = 1000     # 每次最大翻译字符数 (防止误触选中大段文字)

# ========== 翻译方向 ==========
SOURCE_LANG = "auto"       # 源语言: 自动检测
TARGET_LANG = "en"         # 目标语言: 默认英文 (可改为 'zh-CN', 'ja' 等)
# 注意: 青春版硬编码了目标语言，专业版支持菜单切换

# ========== 无状态配置 (Stateless) ==========
def ensure_user_data():
    """
    青春版特性: 不在用户目录生成任何缓存或配置文件，
    保持极致干净，即开即用，即删即净。
    """
    pass

def get_config_status():
    return {"status": "BasicVersion Loaded", "mode": "Stateless"}
