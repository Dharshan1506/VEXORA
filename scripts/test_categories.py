import urllib.request
import json

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/auth/login',
    data=json.dumps({'email': 'admin@vexora.edu', 'password': 'Admin@2026'}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
with urllib.request.urlopen(req) as resp:
    token = json.loads(resp.read().decode('utf-8'))['token']

categories = ['All', 'Academic', 'Examination', 'Hostel', 'Placement', 'Rules', 'General']
for cat in categories:
    url = 'http://127.0.0.1:8000/api/documents' if cat == 'All' else f'http://127.0.0.1:8000/api/documents?category={cat}'
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        docs = data.get('documents', [])
        print(f"Category [{cat}]: {len(docs)} documents")
        for d in docs:
            print(f"   - {d.get('name')} | Cat: {d.get('category')} | Ver: {d.get('version')} | Chunks: {d.get('total_chunks')}")
