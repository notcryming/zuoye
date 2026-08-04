'''
本项目需要的配置：
1.数据库地址，连接到数据库的地址，例如SQLite，数据库的路径
2.JWT认证配置，用于生成和验证，JWT令牌的密钥、算法和过期时间
3.其他配置，根据项目需求添加其他配置项，如日志级别、缓存配置等。
'''
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    '''
    应用配置类，包含数据库地址、JWT认证配置等
    '''
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra="ignore")

    # 属性名都需要大写，并且与.env中的变量名一致，每个属性名都需要加上类型校验
    APP_NAME: str = "保险精准营销系统"
    DATABASE_URL: str = "sqlite:///./instance/starter.db"

    # JWT认证（教学骨架核心配置）
    JWT_SECRET_KEY: str = 'jwt-secret-change-me'     # 生产环境务必在 .env 覆盖成随机串
    JWT_ALGORITHM: str = 'HS256'                    # 算法：HS256，对称加密算法--验和签都是用一个密钥
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24   # 默认 1 天

    # 机器学习模型存储目录（训练产出的 .joblib 文件存放位置）
    MODEL_DIR: str = "data/models"

    # 大模型 LLM 配置（OpenAI 兼容协议，通义千问 qwen-flash）
    # LLM_API_KEY 留空时自动降级：client=None，调用返回 success=False
    LLM_API_KEY: str = ""
    LLM_API_BASE: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    LLM_MODEL: str = "qwen-flash"

# 模块实例化：import本模块时立即创建一个全局单例
settings = Settings()

