from pydantic import BaseSettings


class Settings(BaseSettings):
    postgres_user: str = "vpn_admin"
    postgres_password: str = "supersecret"
    postgres_db: str = "vpn_billing"
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    redis_host: str = "redis"
    redis_port: int = 6379
    minio_endpoint: str = "http://minio:9000"
    minio_root_user: str = "admin"
    minio_root_password: str = "changeme123"
    minio_bucket: str = "configs"
    telegram_payment_provider: str = "stars"
    allowed_origins: str = "*"

    class Config:
        env_file = ".env"
        env_prefix = ""
        case_sensitive = False
        fields = {
            "postgres_user": {"env": "POSTGRES_USER"},
            "postgres_password": {"env": "POSTGRES_PASSWORD"},
            "postgres_db": {"env": "POSTGRES_DB"},
            "postgres_host": {"env": "POSTGRES_HOST"},
            "postgres_port": {"env": "POSTGRES_PORT"},
            "redis_host": {"env": "REDIS_HOST"},
            "redis_port": {"env": "REDIS_PORT"},
            "minio_endpoint": {"env": "MINIO_ENDPOINT"},
            "minio_root_user": {"env": "MINIO_ROOT_USER"},
            "minio_root_password": {"env": "MINIO_ROOT_PASSWORD"},
            "minio_bucket": {"env": "MINIO_BUCKET"},
            "telegram_payment_provider": {"env": "TELEGRAM_PAYMENT_PROVIDER"},
            "allowed_origins": {"env": "ALLOWED_ORIGINS"},
        }


def get_settings() -> Settings:
    return Settings()
