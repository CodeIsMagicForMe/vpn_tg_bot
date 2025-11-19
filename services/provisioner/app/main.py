from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from .amnezia import build_profile
from .config import get_settings
from .schemas import ProvisionRequest, ProvisionResponse

app = FastAPI(title="Provisioner Service", version="0.1.0")
settings = get_settings()

SAMPLE_CONFIGS = {
    "wireguard": "[Interface]\nPrivateKey=CHANGEME...",
    "openvpn": "client\nproto udp\nremote vpn.example.com 1194",
}

TARIFF_LIMITS = {
    "trial": {"max_simultaneous": 2, "traffic_cap_gb": 50},
    "light": {"max_simultaneous": 3, "traffic_cap_gb": 500},
    "family": {"max_simultaneous": 6, "traffic_cap_gb": 1500},
    "unlimited": {"max_simultaneous": 12, "traffic_cap_gb": 3000},
    "default": {"max_simultaneous": 2, "traffic_cap_gb": 200},
}

TARIFF_SPEEDS = {
    "trial": None,
    "light": 100,
    "family": 300,
    "unlimited": None,
}

QR_BASE = "https://api.qrserver.com/v1/create-qr-code/?size=200x200&data="


@app.get("/health")
def health():
    return {"status": "ok", "bucket": settings.minio_bucket}


@app.post("/provision", response_model=ProvisionResponse)
def provision(req: ProvisionRequest):
    limits = TARIFF_LIMITS.get(req.tariff_code, TARIFF_LIMITS["default"])
    if req.simultaneous_use >= limits["max_simultaneous"]:
        raise HTTPException(status_code=429, detail="Too many simultaneous connections")
    if req.traffic_usage_gb >= limits["traffic_cap_gb"]:
        raise HTTPException(status_code=403, detail="Traffic cap exceeded")

    if req.protocol == "amneziawg":
        config = build_profile(
            public_host=settings.amnezia_public_host,
            public_port=settings.amnezia_public_port,
            device_name=req.device_name,
        )
    else:
        config = SAMPLE_CONFIGS.get(req.protocol, "")
    expires = datetime.utcnow() + timedelta(hours=1)
    return ProvisionResponse(
        protocol=req.protocol,
        config=config + f"\n# device={req.device_name}",
        qr_url=f"{QR_BASE}{req.device_name}-{req.protocol}",
        expires_at=expires,
        speed_limit_mbps=TARIFF_SPEEDS.get(req.tariff_code),
    )
