"""
IP geolocation via ip-api.com free tier (no key, 45 req/min limit — fine for a
prototype; swap GEO_API_BASE for a paid provider like ipinfo.io/MaxMind for
production, the response shape will need adjusting).
"""
import logging
import time

import requests

from app.config import settings

logger = logging.getLogger(__name__)

_cache: dict = {}


def geolocate_ip(ip: str) -> dict:
    if ip in _cache:
        return _cache[ip]

    fields = "status,message,country,regionName,city,lat,lon,isp,org,proxy,query"
    url = f"{settings.GEO_API_BASE}/{ip}?fields={fields}"

    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "success":
            result = {"ip": ip, "error": data.get("message", "lookup failed")}
        else:
            result = {
                "ip": ip,
                "country": data.get("country"),
                "region": data.get("regionName"),
                "city": data.get("city"),
                "lat": data.get("lat"),
                "lon": data.get("lon"),
                "isp": data.get("isp"),
                "org": data.get("org"),
                "is_proxy": bool(data.get("proxy")),
            }
        _cache[ip] = result
        time.sleep(0.05)  # stay well under the 45/min free-tier limit
        return result
    except Exception as e:
        logger.warning("Geolocation failed for %s: %s", ip, e)
        return {"ip": ip, "error": str(e)}


def geolocate_many(ips: list) -> list:
    return [geolocate_ip(ip) for ip in ips]
