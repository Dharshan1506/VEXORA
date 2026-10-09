import urllib.request
import json

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/auth/login',
    data=json.dumps({'email': 'admin@vexora.edu', 'password': 'Admin@2026'}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
with urllib.request.urlopen(req) as resp:
    token = json.loads(resp.read().decode('utf-8'))['token']

req = urllib.request.Request('http://127.0.0.1:8000/api/documents/suggested-queries',
    headers={'Authorization': f'Bearer {token}'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode('utf-8'))
    for s in data.get('suggestions', []):
        print(f"[{s['id']}] {s['title']} | Badge: {s['badge']} | Evidence: {s['has_evidence']} | Doc: {s['source_doc']}")
