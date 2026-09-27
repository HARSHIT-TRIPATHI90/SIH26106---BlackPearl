"""
Parses raw .eml bytes into structured data: headers, body, SPF/DKIM/DMARC
verdicts (read from Authentication-Results / Received-SPF headers, NOT
re-verified against DNS — a hackathon prototype has no business re-implementing
RFC 7208/6376 DNS verification; it reads what the receiving mail server already
computed, which is what every SOC tool does), relay path from Received headers,
and IOC extraction (IPs, domains, URLs).
"""
import re
from email import message_from_bytes, policy
from email.utils import parseaddr


IP_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"
)
URL_RE = re.compile(r"https?://[^\s\"'<>\)\]]+", re.IGNORECASE)
DOMAIN_RE = re.compile(
    r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b"
)

# domains that show up in every email and are noise, not IOCs
DOMAIN_ALLOWLIST = {
    "w3.org", "schema.org", "gmail.com", "googlemail.com", "google.com",
    "outlook.com", "microsoft.com", "yahoo.com", "apple.com",
}


def _extract_auth_results(headers: dict) -> dict:
    """Pull SPF/DKIM/DMARC verdicts out of Authentication-Results / Received-SPF."""
    auth_header = headers.get("Authentication-Results", "") or ""
    received_spf = headers.get("Received-SPF", "") or ""

    def find_verdict(pattern: str, text: str) -> str:
        m = re.search(pattern, text, re.IGNORECASE)
        return m.group(1).lower() if m else "none"

    spf = find_verdict(r"spf=(\w+)", auth_header) 
    if spf == "none" and received_spf:
        spf = find_verdict(r"^(\w+)", received_spf.strip())

    dkim = find_verdict(r"dkim=(\w+)", auth_header)
    dmarc = find_verdict(r"dmarc=(\w+)", auth_header)

    return {"spf": spf, "dkim": dkim, "dmarc": dmarc, "raw": auth_header or received_spf}


def _extract_relay_path(msg) -> list:
    """
    Received headers are stacked newest-first (top = last hop before you).
    We reverse them so index 0 = originating server, last = final delivery.
    """
    received_headers = msg.get_all("Received", []) or []
    hops = []
    for hop in reversed(received_headers):
        ip_match = IP_RE.search(hop)
        from_match = re.search(r"from\s+(\S+)", hop, re.IGNORECASE)
        by_match = re.search(r"by\s+(\S+)", hop, re.IGNORECASE)
        hops.append({
            "raw": hop.strip(),
            "from": from_match.group(1) if from_match else None,
            "by": by_match.group(1) if by_match else None,
            "ip": ip_match.group(0) if ip_match else None,
        })
    return hops


def _detect_anomalies(headers: dict, from_addr: str, reply_to: str, return_path: str, auth: dict) -> list:
    anomalies = []

    from_domain = from_addr.split("@")[-1].lower() if "@" in from_addr else ""
    reply_domain = reply_to.split("@")[-1].lower() if "@" in reply_to else ""
    return_domain = return_path.split("@")[-1].lower() if "@" in return_path else ""

    if reply_domain and from_domain and reply_domain != from_domain:
        anomalies.append(f"Reply-To domain ({reply_domain}) differs from From domain ({from_domain}) — classic BEC/phishing redirect pattern")

    if return_domain and from_domain and return_domain != from_domain:
        anomalies.append(f"Return-Path domain ({return_domain}) differs from From domain ({from_domain}) — possible spoofing")

    if auth["spf"] in ("fail", "softfail"):
        anomalies.append(f"SPF check {auth['spf']} — sending IP not authorized for {from_domain}")
    if auth["dkim"] == "fail":
        anomalies.append("DKIM signature failed — message content/headers may have been altered in transit")
    if auth["dmarc"] == "fail":
        anomalies.append("DMARC alignment failed — sender identity could not be verified")

    display_name = headers.get("From", "")
    if "<" in display_name:
        name_part = display_name.split("<")[0].strip().strip('"')
        if name_part and "@" in name_part and name_part.lower() != from_addr.lower():
            anomalies.append(f"Display name contains an email-like string ({name_part}) different from actual From address — impersonation attempt")

    return anomalies


# these headers are packed with key=value forensic syntax (header.from=,
# smtp.mailfrom=, dkim d=/s=/bh=/b=...) that looks like dotted domains to a
# naive regex but isn't — scan them for IPs only, never for domains.
DOMAIN_SCAN_EXCLUDED_HEADERS = {
    "authentication-results", "received-spf", "dkim-signature",
    "arc-authentication-results", "arc-message-signature", "arc-seal",
}


def extract_iocs(headers: dict, body_text: str, relay_path: list) -> dict:
    full_haystack = "\n".join([str(v) for v in headers.values()]) + "\n" + (body_text or "")
    domain_haystack = "\n".join(
        str(v) for k, v in headers.items() if k.lower() not in DOMAIN_SCAN_EXCLUDED_HEADERS
    ) + "\n" + (body_text or "")

    ips = set(IP_RE.findall(full_haystack))
    for hop in relay_path:
        if hop.get("ip"):
            ips.add(hop["ip"])
    # strip private/loopback ranges — not useful forensic IOCs
    ips = {ip for ip in ips if not (
        ip.startswith("127.") or ip.startswith("10.") or ip.startswith("192.168.")
        or ip.startswith("172.16.") or ip == "0.0.0.0"
    )}

    urls = set(URL_RE.findall(body_text or ""))

    domains = set()
    for url in urls:
        m = re.search(r"https?://([^/:\s]+)", url)
        if m:
            domains.add(m.group(1).lower())
    for d in DOMAIN_RE.findall(domain_haystack):
        d = d.lower().strip(".")
        if d not in DOMAIN_ALLOWLIST and len(d.split(".")) >= 2:
            domains.add(d)

    return {"ips": sorted(ips), "domains": sorted(domains), "urls": sorted(urls)}


def parse_eml(raw_bytes: bytes) -> dict:
    msg = message_from_bytes(raw_bytes, policy=policy.default)

    headers = {k: v for k, v in msg.items()}

    from_addr = parseaddr(headers.get("From", ""))[1]
    reply_to = parseaddr(headers.get("Reply-To", ""))[1]
    return_path = parseaddr(headers.get("Return-Path", ""))[1]
    to_addr = parseaddr(headers.get("To", ""))[1]
    subject = headers.get("Subject", "")

    auth = _extract_auth_results(headers)
    relay_path = _extract_relay_path(msg)
    anomalies = _detect_anomalies(headers, from_addr, reply_to, return_path, auth)

    body_text = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/plain" and not part.get_filename():
                try:
                    body_text += part.get_content()
                except Exception:
                    pass
        if not body_text:
            for part in msg.walk():
                if part.get_content_type() == "text/html" and not part.get_filename():
                    try:
                        body_text += part.get_content()
                    except Exception:
                        pass
    else:
        try:
            body_text = msg.get_content()
        except Exception:
            body_text = str(msg.get_payload())

    iocs = extract_iocs(headers, body_text, relay_path)

    return {
        "headers": headers,
        "subject": subject,
        "from_addr": from_addr,
        "sender_domain": from_addr.split("@")[-1].lower() if "@" in from_addr else "",
        "to_addr": to_addr,
        "reply_to": reply_to,
        "return_path": return_path,
        "body_text": body_text[:20000],  # cap for sanity / Gemini token budget
        "spf": auth["spf"],
        "dkim": auth["dkim"],
        "dmarc": auth["dmarc"],
        "relay_path": relay_path,
        "auth_anomalies": anomalies,
        "iocs": iocs,
    }
