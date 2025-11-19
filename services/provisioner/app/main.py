from datetime import datetime, timedelta
from fastapi import FastAPI
from .config import get_settings
from .schemas import ProvisionRequest, ProvisionResponse

app = FastAPI(title="Provisioner Service", version="0.1.0")
settings = get_settings()

SAMPLE_CONFIGS = {
    "amneziawg": "[Interface]\nPrivateKey=CHANGEME...",
    "wireguard": "[Interface]\nPrivateKey=CHANGEME...",
    "openvpn": "client\nproto udp\nremote vpn.example.com 1194",
}

QR_BASE = "https://api.qrserver.com/v1/create-qr-code/?size=200x200&data="


@app.get("/health")
def health():
    return {"status": "ok", "bucket": settings.minio_bucket}


@app.post("/provision", response_model=ProvisionResponse)
def provision(req: ProvisionRequest):
    config = SAMPLE_CONFIGS.get(req.protocol, "")
    expires = datetime.utcnow() + timedelta(hours=1)
    return ProvisionResponse(
        protocol=req.protocol,
        config=config + f"\n# device={req.device_name}",
        qr_url=f"{QR_BASE}{req.device_name}-{req.protocol}",
        expires_at=expires,
        speed_limit_mbps=100 if req.tariff_code == "light" else None,
    )
