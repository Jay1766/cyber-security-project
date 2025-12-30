import socket
import requests
import subprocess
import platform
import re
import time
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor

COMMON_PORTS = {
    21: "FTP",
    22: "SSH",
    80: "HTTP",
    443: "HTTPS",
    3306: "MySQL",
    8080: "HTTP-Alt"
}

def get_target_domain_ip(target):
    """Parses target URL/IP and resolves to an IP address."""
    try:
        if target.startswith("http://") or target.startswith("https://"):
            parsed = urlparse(target)
            hostname = parsed.netloc
        else:
            hostname = target
        
        if ":" in hostname:
            hostname = hostname.split(":")[0]
            
        ip_address = socket.gethostbyname(hostname)
        return hostname, ip_address
    except Exception as e:
        return None, None

def detect_os_ttl(ip_address):
    """Detects OS based on Ping TTL value."""
    try:
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        # Reduced timeout for speed
        command = ['ping', param, '1', '-w', '1000', ip_address] if platform.system().lower() == 'windows' else ['ping', param, '1', '-W', '1', ip_address]
        
        output = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        result = output.stdout
        
        if output.returncode != 0:
            return "Unknown (Ping Blocked)"

        ttl_match = re.search(r'ttl[= ]?(\d+)', result, re.IGNORECASE)
        
        if ttl_match:
            ttl = int(ttl_match.group(1))
            if ttl <= 64: return f"Linux/Unix (TTL={ttl})"
            elif ttl <= 128: return f"Windows (TTL={ttl})"
            elif ttl <= 255: return f"Network Device (TTL={ttl})"
            else: return f"Unknown (TTL={ttl})"
        else:
            return "Unknown (No TTL)"
    except:
        return "Unknown"

def get_port_risk(port, state, service):
    if state == "Closed": return "Safe"
    if port == 21: return "High"
    if port == 22: return "Medium"
    if port == 80: return "Medium"
    if port == 443: return "Low"
    if port == 3306: return "High"
    if port == 8080: return "Medium"
    return "Low"

def get_recommendation(port, service, risk):
    """Generates a recommendation based on the port and service."""
    if risk == "Safe": return "None required."
    
    if port == 21: return "Replace FTP with SFTP/SCP to encrypt traffic."
    if port == 22: return "Ensure SSH is configured with key-based auth and root login disabled."
    if port == 80: return "Redirect all HTTP traffic to HTTPS (port 443)."
    if port == 443: return "Ensure strong TLS ciphers are enabled."
    if port == 3306: return "Bind MySQL to localhost or use a VPN. Do not expose to public internet."
    if port == 8080: return "Restrict access to administrative interfaces (VPN/IP allowlist)."
    
    return "Review service configuration and firewall rules."

def scan_port(ip, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        result = s.connect_ex((ip, port))
        s.close()
        
        service = COMMON_PORTS.get(port, "Unknown")
        state = "Open" if result == 0 else "Closed"
        risk = get_port_risk(port, state, service)
        recommendation = get_recommendation(port, service, risk)
        
        return {
            "port": port,
            "state": state,
            "service": service,
            "risk": risk,
            "recommendation": recommendation
        }
    except:
        return {
            "port": port,
            "state": "Closed",
            "service": COMMON_PORTS.get(port, "Unknown"),
            "risk": "Safe",
            "recommendation": "None"
        }

def analyze_web_headers(target):
    findings = []
    server_info = "Unknown"
    if not target.startswith("http"): target = "http://" + target
    try:
        response = requests.head(target, timeout=3, allow_redirects=True)
        headers = response.headers
        server_info = headers.get("Server", "Unknown")
        
        if "X-Powered-By" in headers:
            findings.append({
                "type": "Info", 
                "message": f"Technology disclosed: {headers['X-Powered-By']}", 
                "risk": "Low",
                "recommendation": "Remove 'X-Powered-By' header to prevent info leakage."
            })
            
        if target.startswith("https") and "Strict-Transport-Security" not in headers:
             findings.append({
                 "type": "Security", 
                 "message": "HSTS Header Missing", 
                 "risk": "Medium",
                 "recommendation": "Enable HSTS (Strict-Transport-Security) to enforce HTTPS."
             })
             
        if "Server" in headers:
             findings.append({
                "type": "Info", 
                "message": f"Server banner exposed: {server_info}", 
                "risk": "Low",
                "recommendation": "Configure server to suppress detailed version banners."
            })

    except: pass
    # Ensure headers is a dict if it wasn't set
    if 'headers' not in locals(): headers = {}
    return server_info, findings, dict(headers)

def calculate_overall_risk(open_ports, vulnerabilities):
    score = 0
    for p in open_ports:
        if p['state'] == 'Open':
            if p['risk'] == "High": score += 3
            elif p['risk'] == "Medium": score += 2
            else: score += 1
            
    for v in vulnerabilities:
        if v['risk'] == "High": score += 5
        elif v['risk'] == "Medium": score += 3
        
    if score >= 10: return "High"
    elif score >= 5: return "Medium"
    return "Low"

def perform_scan(target):
    start_time = time.time()
    hostname, ip = get_target_domain_ip(target)
    
    if not ip:
        return {"error": "Could not resolve hostname"}
    
    os_guess = detect_os_ttl(ip)
    
    scan_results = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(scan_port, ip, port) for port in COMMON_PORTS.keys()]
        for future in futures:
            res = future.result()
            if res: scan_results.append(res)
    scan_results.sort(key=lambda x: x['port'])

    web_analysis = {"server": "Unknown", "headers": {}}
    vulnerabilities = []
    open_ports = [p['port'] for p in scan_results if p['state'] == 'Open']
    
    # Generate vulnerabilities from Open Ports
    for p in scan_results:
        if p['state'] == 'Open':
            vulnerabilities.append({
                "type": f"Open Port {p['port']}",
                "message": f"Service {p['service']} is exposed.",
                "risk": p['risk'],
                "recommendation": p['recommendation']
            })

    if 80 in open_ports or 443 in open_ports:
        server, vulns, headers = analyze_web_headers(target)
        web_analysis["server"] = server
        web_analysis["headers"] = headers
        vulnerabilities.extend(vulns)
        
    risk_level = calculate_overall_risk(scan_results, vulnerabilities)
    duration = round(time.time() - start_time, 2)
    
    ai_summary = f"Detected {os_guess}. "
    if risk_level == "High":
        ai_summary += "CRITICAL: Multiple high-profile services exposed. Immediate hardening of MySQL/FTP required."
    elif risk_level == "Medium":
        ai_summary += "WARNING: Insecure services (HTTP/SSH) detected. Review firewall and encryption policies."
    else:
        ai_summary += "Target security posture appears solid based on standard vectors."

    return {
        "target": target,
        "hostname": hostname,
        "ip": ip,
        "os_guess": os_guess,
        "scan_results": scan_results,
        "web_analysis": web_analysis,
        "vulnerabilities": vulnerabilities,
        "risk_level": risk_level,
        "metadata": {
            "duration": f"{duration}s",
            "total_ports": len(COMMON_PORTS),
            "open_count": len(open_ports),
            "scan_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time))
        },
        "ai_summary": ai_summary
    }
