#!/usr/bin/env python3
"""
Image Generation Service — poort 11436
POST /generate  { prompt, backend, model, replicate_key?, width?, height?, steps? }
GET  /health
"""
import http.server, json, base64, os, time, tempfile, urllib.request

PORT = 11436

REPLICATE_MODELS = {
    'sdxl':         'stability-ai/sdxl',
    'flux-schnell': 'black-forest-labs/flux-schnell',
    'flux-dev':     'black-forest-labs/flux-dev',
}

_pipe = None
_pipe_model = None

def load_local_pipe(model_id='stabilityai/stable-diffusion-xl-base-1.0'):
    global _pipe, _pipe_model
    if _pipe is not None and _pipe_model == model_id:
        return _pipe
    import torch
    from diffusers import StableDiffusionXLPipeline
    print('[image-gen] Laden: ' + model_id, flush=True)
    _pipe = StableDiffusionXLPipeline.from_pretrained(
        model_id, torch_dtype=torch.float32, use_safetensors=True
    )
    _pipe.set_progress_bar_config(disable=True)
    _pipe_model = model_id
    print('[image-gen] Model geladen', flush=True)
    return _pipe

def generate_local(prompt, steps=20, width=1024, height=1024):
    pipe = load_local_pipe()
    image = pipe(prompt, num_inference_steps=steps, width=width, height=height).images[0]
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        image.save(f.name)
        path = f.name
    with open(path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
    os.unlink(path)
    return b64

def generate_replicate(prompt, model, api_key, width=1024, height=1024):
    model_id = REPLICATE_MODELS.get(model, REPLICATE_MODELS['flux-schnell'])
    steps = 4 if 'schnell' in model else 28
    payload = json.dumps({
        'input': {'prompt': prompt, 'width': width, 'height': height,
                  'num_inference_steps': steps}
    }).encode()
    req = urllib.request.Request(
        'https://api.replicate.com/v1/models/' + model_id + '/predictions',
        data=payload,
        headers={
            'Authorization': 'Bearer ' + api_key,
            'Content-Type': 'application/json',
            'Prefer': 'wait=60'
        }
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=120).read())
    pred_id = resp.get('id')
    for _ in range(120):
        status = resp.get('status')
        if status == 'succeeded':
            img_url = resp['output']
            if isinstance(img_url, list):
                img_url = img_url[0]
            img_data = urllib.request.urlopen(img_url, timeout=30).read()
            return base64.b64encode(img_data).decode()
        elif status in ('failed', 'canceled'):
            raise Exception('Replicate mislukt: ' + str(resp.get('error')))
        time.sleep(3)
        poll = urllib.request.Request(
            'https://api.replicate.com/v1/predictions/' + pred_id,
            headers={'Authorization': 'Bearer ' + api_key}
        )
        resp = json.loads(urllib.request.urlopen(poll, timeout=30).read())
    raise Exception('Replicate timeout na 6 minuten')

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'ok')
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path != '/generate':
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length))
        prompt        = body.get('prompt', '')
        backend       = body.get('backend', 'local')
        model         = body.get('model', 'sdxl')
        replicate_key = body.get('replicate_key', '')
        width         = int(body.get('width', 1024))
        height        = int(body.get('height', 1024))
        steps         = int(body.get('steps', 20))
        try:
            if backend == 'replicate':
                if not replicate_key:
                    raise Exception('Replicate API-key ontbreekt')
                b64 = generate_replicate(prompt, model, replicate_key, width, height)
            else:
                b64 = generate_local(prompt, steps, width, height)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'image_base64': b64, 'format': 'png'}).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

print('[image-gen] Service gestart op poort ' + str(PORT), flush=True)
http.server.HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
