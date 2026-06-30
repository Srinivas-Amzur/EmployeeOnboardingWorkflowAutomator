"""
Force asyncpg to use IPv4 connections instead of IPv6.
This module patches the connection behavior to work around Windows DNS issues.
"""

import asyncio
import socket
from typing import Optional

async def resolve_hostname_ipv4(hostname: str, port: int = 5432) -> Optional[str]:
    """
    Resolve hostname to IPv4 address, bypassing IPv6.
    
    Args:
        hostname: Database hostname
        port: Port number
        
    Returns:
        IPv4 address if found, None otherwise
    """
    try:
        loop = asyncio.get_event_loop()
        # Force AF_INET to only resolve IPv4
        addr_info = await loop.getaddrinfo(
            hostname, port, 
            family=socket.AF_INET,  # IPv4 only
            type=socket.SOCK_STREAM
        )
        if addr_info:
            ipv4_addr = addr_info[0][4][0]
            print(f"[IPv4 FIX] Resolved {hostname} → {ipv4_addr}")
            return ipv4_addr
    except Exception as e:
        print(f"[IPv4 FIX] Resolution failed: {e}")
    
    return None


def patch_asyncpg_for_ipv4():
    """
    Patch asyncpg to force IPv4 connections.
    Call this before creating the database engine.
    """
    try:
        import asyncpg
        original_connect = asyncpg.connect
        
        async def ipv4_connect(dsn, **kwargs):
            """Wrapper that forces IPv4 resolution."""
            from urllib.parse import urlparse
            
            # Parse DSN to extract hostname
            try:
                # Typical format: postgresql+asyncpg://user:pass@host:port/db
                parts = dsn.split('@')
                if len(parts) >= 2:
                    host_part = parts[-1].split('/')[0]
                    hostname, _, port_str = host_part.partition(':')
                    port = int(port_str) if port_str else 5432
                    
                    # Try to resolve to IPv4
                    ipv4_addr = await resolve_hostname_ipv4(hostname, port)
                    if ipv4_addr:
                        # Replace hostname with IPv4
                        dsn = dsn.replace(hostname, ipv4_addr)
            except Exception as e:
                print(f"[IPv4 FIX] DSN parsing error: {e}")
            
            return await original_connect(dsn, **kwargs)
        
        asyncpg.connect = ipv4_connect
        print("[IPv4 FIX] asyncpg patched for IPv4-only connections")
    except ImportError:
        print("[IPv4 FIX] asyncpg not imported yet, patch will be applied later")
    except Exception as e:
        print(f"[IPv4 FIX] Patching failed: {e}")
