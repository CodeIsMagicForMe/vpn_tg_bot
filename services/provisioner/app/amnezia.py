"""Simplified AmneziaWG config generator placeholder."""

from textwrap import dedent


def build_profile(public_host: str, public_port: int, device_name: str) -> str:
    """Return a mock Amnezia configuration string.

    In production this would call the dedicated Amnezia container API to mint
    Cloak/OpenVPN-over-TLS credentials.
    """

    return dedent(
        f"""
        # AmneziaWG profile generated for {device_name}
        [Interface]
        PrivateKey = <generated>
        Address = 10.7.0.2/32
        DNS = 1.1.1.1

        [Peer]
        PublicKey = <amnezia-public-key>
        Endpoint = {public_host}:{public_port}
        AllowedIPs = 0.0.0.0/0, ::/0
        CloakTransport = openvpn-over-tls
        """
    ).strip()
