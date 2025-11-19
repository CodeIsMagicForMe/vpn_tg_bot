from datetime import datetime
from pydantic import BaseModel
from typing import Literal


Protocol = Literal["amneziawg", "wireguard", "openvpn"]


class ProvisionRequest(BaseModel):
    user_id: int
    protocol: Protocol
    device_name: str
    tariff_code: str
    simultaneous_use: int = 0
    traffic_usage_gb: float = 0.0


class ProvisionResponse(BaseModel):
    protocol: Protocol
    config: str
    qr_url: str
    expires_at: datetime
    speed_limit_mbps: int | None = None
