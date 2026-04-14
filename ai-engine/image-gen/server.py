#!/usr/bin/env python3
"""
Image Generation Service — poort 11436
POST /generate  { prompt, backend, model, replicate_key?, width?, height?, steps? }
GET  /health
"""
import http.server, json, base64, os, time, tempfile, urllib.request

PORT = 11436

# Lokale modellen: naam → (huggingface_id, pipeline_klasse, standaard_steps)
LOCAL_MODELS = {
    'sdxl':       ('stabilityai/stable-diffusion-xl-base-1.0', 'sdxl', 20),
    'sdxl-turbo': ('stabilityai/sdxl-turbo',                   'sdxl', 4),
    'sd15':       ('runwayml/stable-diffusion-v1-5',           'sd15', 20),
}

REPLICATE_MODELS = {
    'sdxl':         'stability-ai/sdxl',
    'flux-schnell': 'black-forest-labs/flux-schnell',
    'flux-dev':     'black-forest-labs/flux-dev',
}

_pipe = None
_pipe_model = None

def load_local_pipe(model_key):
    global _pipe, _pipe_model
    if _pipe is not None and _pipe_model == model_key:
        return _pipe

    model_id, pipeline_type, _ = LOCAL_MODELS.get(model_key, LOCAL_MODELS['sdxl'])
    import torch

    print('[image-gen] Laden: ' + model_id, flush=True)
    if pipeline_type == 'sd15':
        from diffusers import StableDiffusionPipeline
        _pipe = StableDiffusionPipeline.from_pretrained(
            model_id, torch_dtype=torch.float32
        )
    else:
        from diffusers import StableDiffusionXLPipeline
        _pipe = StableDiffusionXLPipeline.from_pretrained(
            model_id, torch_dtype=torch.float32, use_safetensors=True
        )
    _pipe.set_progress_bar_config(disable=True)
    _pipe_model = model_key
    print('[image-gen] Model geladen', flush=True)
    return _pipe

def generate_local(prompt, model='sdxl', steps=None, width=1024, height=1024):
    _, _, default_steps = LOCAL_MODELS.get(model, LOCAL_MODELS['sdxl'])
    actual_steps = steps if steps is not None else default_steps
    # SD 1.5 ondersteunt max 512×512 goed; SDXL 1024×1024
    if model == 'sd15':
        width, height = min(width, 512), min(height, 512)
    pipe = load_local_pipe(model)
    image = pipe(prompt, num_inference_steps=actual_steps, width=width, height=height).images[0]
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
        steps         = body.get('steps')
        steps         = int(steps) if steps is not None else None
        try:
            if backend == 'replicate':
                if not replicate_key:
                    raise Exception('Replicate API-key ontbreekt')
                b64 = generate_replicate(prompt, model, replicate_key, width, height)
            else:
                b64 = generate_local(prompt, model, steps, width, height)
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
