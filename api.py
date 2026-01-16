import socket
import os
import re
from dotenv import load_dotenv
import asyncio
import aiohttp
import database 

# --- Load .env file to make sure keys are available ---
load_dotenv()

# --- DNS Patching ---
HOST_IP_MAP = {
    "www.ipqualityscore.com": "104.18.12.18",
    "otx.alienvault.com": "34.239.115.143"
}
for host in HOST_IP_MAP:
    try:
        HOST_IP_MAP[host] = socket.gethostbyname(host)
    except socket.gaierror:
        print(f"Warning: DNS resolution failed for {host}. Using fallback IP.")

class CustomResolver(aiohttp.abc.AbstractResolver):
    async def resolve(self, host, port, family=socket.AF_INET):
        if host in HOST_IP_MAP:
            ip = HOST_IP_MAP[host]
            return [{'hostname': host, 'host': ip, 'port': port, 'family': family, 'proto': 0, 'flags': 0}]
        loop = asyncio.get_event_loop()
        return await loop.getaddrinfo(host, port, family=family)

    async def close(self):
        pass

def extract_ips_from_file(filepath):
    """ Reads a file and extracts all unique IPv4 addresses using regex. """
    IP_REGEX = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            ips = re.findall(IP_REGEX, content)
            return list(set(ips))
    except Exception as e:
        print(f"Error reading or processing file: {e}")
        return []

# --- API Key Getters ---
def get_ipqs_api_key():
    key = os.getenv('IPQS_API_KEY')
    return key.strip() if key else None

def get_otx_api_key():
    key = os.getenv('OTX_API_KEY')
    return key.strip() if key else None

# --- ASYNCHRONOUS API Calls ---
async def get_ipqs_reputation_async(session, ip_address):
    api_key = get_ipqs_api_key()
    if not api_key: return {'error': 'IPQS Key not set.'}
    
    full_url = f"https://www.ipqualityscore.com/api/json/ip/{api_key}/{ip_address}"
    params = {'strictness': 0, 'allow_public_access_points': 'true'}
    try:
        async with session.get(full_url, params=params, timeout=20) as response:
            response.raise_for_status()
            data = await response.json()
            if not data.get('success', False):
                return {'error': data.get('message', 'Unknown API error')}
            return {'data': data}
    except Exception as e:
        return {'error': f'API request failed: {e}'}

async def get_otx_pulse_count_async(session, ip_address):
    api_key = get_otx_api_key()
    if not api_key: return 0
    
    full_url = f"https://otx.alienvault.com/api/v1/indicators/IPv4/{ip_address}/general"
    headers = {'X-OTX-API-KEY': api_key}
    try:
        async with session.get(full_url, headers=headers, timeout=20) as response:
            if response.status == 404: return 0
            response.raise_for_status()
            data = await response.json()
            return data.get('pulse_info', {}).get('count', 0)
    except Exception:
        return -1

async def get_ipqs_account_stats_async(session):
    """ Fetches account stats like remaining credits from IPQS. """
    api_key = get_ipqs_api_key()
    if not api_key: return {'error': 'IPQS Key not set.'}

    full_url = f"https://www.ipqualityscore.com/api/json/account/{api_key}"
    try:
        async with session.get(full_url, timeout=20) as response:
            response.raise_for_status()
            data = await response.json()
            if not data.get('success', False):
                return {'error': data.get('message', 'Unknown API error')}
            return {'data': data}
    except Exception as e:
        return {'error': f'API request failed: {e}'}

async def process_single_ip_and_save(session, ip_info, api_key_otx, progress_callback):
    """
    Processes a single IP, saves the result to the DB, and returns the IP's ID.
    """
    ip = ip_info['ip']
    existing_details = ip_info['details']
    ip_id = existing_details['id'] if existing_details else None

    ipqs_result = await get_ipqs_reputation_async(session, ip)
    
    if 'data' in ipqs_result:
        data = ipqs_result['data']
        country = data.get("country_code", "N/A")
        score = data.get("fraud_score", 0)
        
        malicious = score >= 85
        
        isp = data.get("ISP", "N/A")
        org = data.get("organization", "N/A")
        
        pulses = -1
        if api_key_otx:
            pulses = await get_otx_pulse_count_async(session, ip)
        
        if ip_id:
            database.update_ip_record_details(ip_id, country, malicious, score, isp, org, pulses)
        else:
            ip_id = database.add_ip_record(ip, country, malicious, score, isp, org, pulses)

        progress_callback({'ip': ip, 'result': {'score': score, 'country': country, 'pulses': pulses}})
        return {'ip_id': ip_id}

    else:
        progress_callback({'ip': ip, 'error': ipqs_result.get('error', 'Unknown')})
        ip_id = database.get_or_create_ip_id(ip)
        return {'ip_id': ip_id}

async def run_concurrent_analysis(ips_to_query, api_key_otx, progress_callback, cancel_event):
    """
    The main entry point for concurrent analysis.
    """
    conn = aiohttp.TCPConnector(resolver=CustomResolver(), ssl=False)
    async with aiohttp.ClientSession(connector=conn, headers={'User-Agent': 'LOCKON IP Prism v2.1'}) as session:
        tasks = []
        for ip_info in ips_to_query:
            if cancel_event.is_set():
                break
            task = asyncio.create_task(process_single_ip_and_save(session, ip_info, api_key_otx, progress_callback))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if r is not None and not isinstance(r, Exception)]
