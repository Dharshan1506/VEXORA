import urllib.request
import json

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/auth/login',
    data=json.dumps({'email': 'admin@vexora.edu', 'password': 'Admin@2026'}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
with urllib.request.urlopen(req) as resp:
    token = json.loads(resp.read().decode('utf-8'))['token']

# 1. Fetch versions dropdown list
req = urllib.request.Request('http://127.0.0.1:8000/api/documents/versions', headers={'Authorization': f'Bearer {token}'})
with urllib.request.urlopen(req) as resp:
    versions_data = json.loads(resp.read().decode('utf-8'))
    print(f"Versions available in dropdown: {len(versions_data['versions'])}")
    for v in versions_data['versions']:
        print(f"  - {v['name']} ({v['version']}) [ID: {v['id']}]")

# Find Academic 2025 and Academic 2026
doc_2025 = next(v for v in versions_data['versions'] if '2025' in v['name'] and 'ACADEMIC' in v['name'].upper())
doc_2026 = next(v for v in versions_data['versions'] if '2026' in v['name'] and 'ACADEMIC' in v['name'].upper())

print(f"\nComparing Source: {doc_2025['name']} ({doc_2025['id']}) vs Target: {doc_2026['name']} ({doc_2026['id']})")

compare_req = urllib.request.Request(
    'http://127.0.0.1:8000/api/documents/compare',
    data=json.dumps({
        'source_document_id': doc_2025['id'],
        'target_document_id': doc_2026['id']
    }).encode('utf-8'),
    headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
)

with urllib.request.urlopen(compare_req) as resp:
    comp_result = json.loads(resp.read().decode('utf-8'))
    print("\n--- COMPARISON SUMMARY ---")
    print(f"Source: {comp_result['source_document']['name']} ({comp_result['source_document']['version']})")
    print(f"Target: {comp_result['target_document']['name']} ({comp_result['target_document']['version']})")
    print(f"Total Changes Detected: {len(comp_result['changes'])}")
    print(f"Summary: {comp_result['summary']}")
    
    print("\n--- DETECTED REAL PARAMETER SHIFTS ---")
    for i, c in enumerate(comp_result['changes'][:10], start=1):
        print(f"[{i}] {c['parameter']}: '{c['old_value']}' -> '{c['new_value']}' (Type: {c['type']})")
        if c.get('source_a'):
            print(f"    Source A: Page {c['source_a'].get('page')}, Section: {c['source_a'].get('section')}")
            print(f"    Snippet A: {c['source_a'].get('snippet', '')[:100]}...")
        if c.get('source_b'):
            print(f"    Source B: Page {c['source_b'].get('page')}, Section: {c['source_b'].get('section')}")
            print(f"    Snippet B: {c['source_b'].get('snippet', '')[:100]}...")
