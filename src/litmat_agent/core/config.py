"""项目配置模块"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM配置
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    default_model: str = "gpt-4"

    # 数据源配置
    sciverse_api_key: str = ""
    sciverse_base_url: str = "https://sciverse.opendatalab.com/api"

    # 本地数据路径
    sci_base_data_path: str = "./data/sci_base"

    # 数据库配置
    postgres_url: str = "postgresql://localhost:5432/litmat"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""

    # 系统配置
    max_retrieval_results: int = 20
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # 日志配置
    log_level: str = "INFO"


settings = Settings()
