"""
应用配置管理
使用 pydantic-settings 管理环境变量和配置
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # ===== 数据库配置 =====
    db_type: str = "sqlite"  # sqlite 或 mysql
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = "your_password"
    mysql_database: str = "stock_warehouse"
    sqlite_path: str = "stock_warehouse.db"

    # ===== Redis 配置 =====
    redis_enabled: bool = False  # 开发环境默认关闭
    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0

    # ===== AI 大模型配置 =====
    llm_api_key: str = ""
    llm_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    llm_model_name: str = ""

    # ===== 数据采集配置 =====
    tushare_token: Optional[str] = None
    ths_api_key: Optional[str] = None

    # ===== 服务配置 =====
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False
    log_level: str = "INFO"

    # ===== 定时任务配置 =====
    collect_hour: int = 17
    collect_minute: int = 0

    @property
    def database_url(self) -> str:
        if self.db_type == "sqlite":
            return f"sqlite:///{self.sqlite_path}"
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            f"?charset=utf8mb4"
        )

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "allow",
    }


settings = Settings()