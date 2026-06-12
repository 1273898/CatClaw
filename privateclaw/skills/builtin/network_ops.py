"""Network operations skills implementation."""

import socket
import subprocess
import platform
from typing import Optional
import httpx


SKILL_DEFINITION = {
    "name": "network_ops",
    "description": "Network operations toolkit",
    "category": "network",
    "parameters": {}
}


def http_get(url: str, headers: Optional[dict] = None, timeout: int = 30) -> dict:
    """Make HTTP GET request."""
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(url, headers=headers)

            return {
                "success": True,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response.text,
                "url": str(response.url),
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


def http_post(url: str, data: Optional[dict] = None, headers: Optional[dict] = None,
              content_type: str = "application/json") -> dict:
    """Make HTTP POST request."""
    try:
        with httpx.Client() as client:
            if content_type == "application/json":
                response = client.post(url, json=data, headers=headers)
            else:
                response = client.post(url, data=data, headers=headers)

            return {
                "success": True,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response.text,
                "url": str(response.url),
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_webpage(url: str, extract_text: bool = True, selector: Optional[str] = None) -> dict:
    """Fetch and parse webpage content."""
    try:
        with httpx.Client() as client:
            response = client.get(url)
            html = response.text

            if extract_text:
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, 'html.parser')

                    # Remove script and style elements
                    for element in soup(['script', 'style', 'meta', 'link']):
                        element.decompose()

                    if selector:
                        elements = soup.select(selector)
                        text = "\n".join(el.get_text(strip=True) for el in elements)
                    else:
                        text = soup.get_text(separator='\n', strip=True)

                    return {
                        "success": True,
                        "url": url,
                        "content": text,
                        "title": soup.title.string if soup.title else None,
                    }
                except ImportError:
                    # Fallback: return raw HTML
                    return {
                        "success": True,
                        "url": url,
                        "content": html,
                        "note": "BeautifulSoup not installed, returning raw HTML",
                    }
            else:
                return {
                    "success": True,
                    "url": url,
                    "content": html,
                }
    except Exception as e:
        return {"success": False, "error": str(e)}


def dns_lookup(hostname: str, record_type: str = "A") -> dict:
    """Perform DNS lookup."""
    try:
        import dns.resolver

        answers = dns.resolver.resolve(hostname, record_type)
        records = []

        for answer in answers:
            records.append({
                "type": record_type,
                "value": str(answer),
                "ttl": answers.ttl,
            })

        return {
            "success": True,
            "hostname": hostname,
            "records": records,
        }
    except ImportError:
        # Fallback using socket
        try:
            ip = socket.gethostbyname(hostname)
            return {
                "success": True,
                "hostname": hostname,
                "records": [{"type": "A", "value": ip}],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def port_check(host: str, port: int, timeout: int = 5) -> dict:
    """Check if a port is open."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()

        return {
            "success": True,
            "host": host,
            "port": port,
            "is_open": result == 0,
            "status": "open" if result == 0 else "closed",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def ping(host: str, count: int = 4) -> dict:
    """Ping a host."""
    try:
        param = "-n" if platform.system().lower() == "windows" else "-c"
        command = ["ping", param, str(count), host]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30,
        )

        return {
            "success": True,
            "host": host,
            "output": result.stdout,
            "returncode": result.returncode,
            "is_reachable": result.returncode == 0,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# Export functions
execute = http_get  # Default executor
