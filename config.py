# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class AppConfig:
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///database.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ApiKeyConfig:
    # ZHIPU API 配置
    ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY")
    ZHIPU_BASE_URL = os.getenv("ZHIPU_BASE_URL")
    # QWEN API 配置
    QWEN_API_KEY = os.getenv("QWEN_API_KEY")
    QWEN_BASE_URL = os.getenv("QWEN_BASE_URL")
    # 智能体 API 配置
    DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
    # 长对话智能体
    LONG_SESSION_AGENT_ID = os.getenv("LONG_SESSION_AGENT_ID")

class PromptConfig:
    # 关键词提取配置
    KEYWORD_EXTRACTION_PROMPT = """
    请判断用户问题与中学数学知识点是否相关。如果是，请提取与问题相关的联网搜索关键词。
    如果问题与数学无关，请返回空关键词列表。
    严格按照输出格式：{"related": true/false, "keywords": ["关键词1", "关键词2"]}。"""

