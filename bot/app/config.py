from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl   # эта строчка отдельно
from typing import List


class Settings(BaseSettings):
    bot_token: str
    bot_admin_ids: List[int]
    billing_url: AnyHttpUrl
    provisioner_url: AnyHttpUrl
    dashboard_url: AnyHttpUrl

    class Config:
        env_file = ".env"
        env_prefix = ""
        case_sensitive = False
        fields = {
            "bot_token": {"env": "BOT_TOKEN"},
            "bot_admin_ids": {"env": "BOT_ADMIN_IDS"},
            "billing_url": {"env": "BILLING_URL"},
            "provisioner_url": {"env": "PROVISIONER_URL"},
            "dashboard_url": {"env": "DASHBOARD_URL"},
        }


def get_settings() -> Settings:
    return Settings()
