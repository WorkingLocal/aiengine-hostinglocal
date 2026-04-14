#!/usr/bin/env python3
"""
Stats Service — poort 11435
GET /api/stats  →  { total_gb, used_gb, avail_gb, models, cpu_pct, cpu_cores, cpu_per_core }
"""
import http.server, json, time, urllib.request

PORT = 11435

def read_meminfo():
    info = {}
    with open('/proc/meminfo') as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 2:
                info[parts[0].rstrip(':')] = int(parts[1])
    total = info.get('MemTotal', 0)
    avail = info.get('MemAvailable', 0)
    used  = total - avail
    return round(total / 1024 / 1024, 1), round(used / 1024 / 1024, 1), round(avail / 1024 / 1024, 1)

def read_cpu_stat():
    cores = {}
    with open('/proc/stat') as f:
        for line in f:
            if not line.startswith('cpu'):
                continue
            parts = line.split()
            name = parts[0]
            vals = list(map(int, parts[1:]))
            idle = vals[3] + (vals[4] if len(vals) > 4 else 0)
            total = sum(vals)
            cores[name] = (total, idle)
    return cores

def get_cpu_usage():
    s1 = read_cpu_stat()
    time.sleep(0.5)
    s2 = read_cpu_stat()
    result = {}
    for name in s1:
        t1, i1 = s1[name]
        t2, i2 = s2[name]
        dt = t2 - t1
        di = i2 - i1
        pct = round((1 - di / dt) * 100, 1) if dt > 0 else 0.0
        result[name] = pct
    total_pct = result.pop('cpu', 0.0)
    per_core = [result[k] for k in sorted(result.keys(), key=lambda x: int(x[3:]))]
    return total_pct, len(per_core), per_core

def get_ollama_models():
    try:
        req = urllib.request.Request('http://localhost:11434/api/ps',
                                     headers={'Accept': 'application/json'})
        resp = urllib.request.urlopen(req, timeout=3)
        data = json.loads(resp.read())
        return [m['name'] for m in data.get('models', [])]
    except Exception:
        return []

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_GET(self):
        if self.path != '/api/stats':
            self.send_response(404)
            self.end_headers()
            return
        total, used, avail = read_meminfo()
        cpu_pct, cpu_cores, cpu_per_core = get_cpu_usage()
        models = get_ollama_models()
        payload = json.dumps({
            'total_gb':    total,
            'used_gb':     used,
            'avail_gb':    avail,
            'cpu_pct':     cpu_pct,
            'cpu_cores':   cpu_cores,
            'cpu_per_core': cpu_per_core,
            'models':      models,
        })
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(payload.encode())

print(f'[stats] Service gestart op poort {PORT}', flush=True)
http.server.HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
