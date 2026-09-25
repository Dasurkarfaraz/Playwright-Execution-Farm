import uuid
from typing import Dict
from datetime import datetime


class Tunnel:
    def __init__(self, tunnel_id: str, name: str, local_host: str, local_port: int):
        self.id = tunnel_id
        self.name = name
        self.local_host = local_host
        self.local_port = local_port
        self.status = "active"
        self.created_at = datetime.utcnow()
        self.private_url = f"https://{tunnel_id}.tunnel.local"
        self.public_url = None
        self.access_logs = []
        self.bandwidth_used = 0

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "local": f"{self.local_host}:{self.local_port}",
            "private_url": self.private_url,
            "public_url": self.public_url,
            "created_at": self.created_at.isoformat(),
            "bandwidth_used": self.bandwidth_used
        }


class TunnelManager:
    def __init__(self):
        self.tunnels: Dict[str, Tunnel] = {}

    def create_tunnel(
        self,
        name: str,
        local_host: str,
        local_port: int,
        protocol: str = "http"
    ) -> str:
        """Create tunnel to private UAT"""
        tunnel_id = f"tunnel-{uuid.uuid4().hex[:8]}"
        tunnel = Tunnel(tunnel_id, name, local_host, local_port)
        self.tunnels[tunnel_id] = tunnel

        # In production, integrate with Cloudflare Tunnel or ngrok
        # For now, simulate tunnel creation
        tunnel.public_url = f"https://{tunnel_id}-public.tunnel.dev"

        return tunnel_id

    def get_tunnel(self, tunnel_id: str) -> Tunnel:
        return self.tunnels.get(tunnel_id)

    def list_tunnels(self) -> list:
        return [t.to_dict() for t in self.tunnels.values()]

    def delete_tunnel(self, tunnel_id: str) -> bool:
        if tunnel_id in self.tunnels:
            del self.tunnels[tunnel_id]
            return True
        return False

    def log_access(self, tunnel_id: str, request_info: dict):
        """Log access through tunnel"""
        if tunnel_id in self.tunnels:
            self.tunnels[tunnel_id].access_logs.append({
                "timestamp": datetime.utcnow().isoformat(),
                "info": request_info
            })


# Configuration for different tunnel providers
TUNNEL_PROVIDERS = {
    "cloudflare": {
        "name": "Cloudflare Tunnel",
        "setup": "cloudflare_tunnel",
        "requires_auth": True
    },
    "ngrok": {
        "name": "ngrok",
        "setup": "ngrok_setup",
        "requires_auth": True
    },
    "ssh": {
        "name": "SSH Tunnel",
        "setup": "ssh_tunnel",
        "requires_auth": True
    },
    "local": {
        "name": "Local Only",
        "setup": "local",
        "requires_auth": False
    }
}


class TunnelConfig:
    """Configuration for connecting to private networks"""
    def __init__(self):
        self.provider = "local"
        self.auth_token = None
        self.vpn_config = None
        self.proxy_config = None

    def set_provider(self, provider: str, auth_token: str = None):
        if provider in TUNNEL_PROVIDERS:
            self.provider = provider
            self.auth_token = auth_token
            return True
        return False

    def set_vpn(self, vpn_type: str, credentials: dict):
        """Set VPN credentials for private network access"""
        self.vpn_config = {
            "type": vpn_type,  # wireguard, openvpn, ipsec
            "credentials": credentials
        }

    def set_proxy(self, proxy_url: str, username: str = None, password: str = None):
        """Set proxy for private network access"""
        self.proxy_config = {
            "url": proxy_url,
            "username": username,
            "password": password
        }

    def to_dict(self):
        return {
            "provider": self.provider,
            "vpn_configured": self.vpn_config is not None,
            "proxy_configured": self.proxy_config is not None
        }


# Global instances
tunnel_manager = TunnelManager()
tunnel_config = TunnelConfig()
