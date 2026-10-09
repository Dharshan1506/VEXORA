import urllib.request
import json

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/auth/login',
    data=json.dumps({'email': 'admin@vexora.edu', 'password': 'Admin@2026'}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
with urllib.request.urlopen(req) as resp:
    token = json.loads(resp.read().decode('utf-8'))['token']

queries = [
    ("Hostel", "What are the curfew hours and biometric attendance timings for hostel students?"),
    ("Placement", "What is the minimum CGPA required for campus placement eligibility?"),
    ("Examination", "What is the passing minimum percentage required in the End Semester Examination?"),
    ("Rules", "What is the maximum vehicle speed limit permitted on campus roads?"),
    ("General", "What are the operating hours of the Central Library?"),
]

for cat, q in queries:
    chat_req = urllib.request.Request(
        'http://127.0.0.1:8000/api/chat',
        data=json.dumps({'message': q}).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
    )
    with urllib.request.urlopen(chat_req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        ans = res.get('answer', {})
        print(f"\n========================================================")
        print(f"CATEGORY: {cat}")
        print(f"QUERY: {q}")
        print(f"EVIDENCE STATUS: {ans.get('evidenceStatus')}")
        print(f"VERIFIED: {res.get('verified')}")
        print(f"CITATIONS ({len(ans.get('citations', []))}):")
        for c in ans.get('citations', []):
            print(f"   -> Doc: {c.get('document_name')} | Page: {c.get('page')} | Conf: {c.get('confidence')}")
        print(f"KEY INFO: {ans.get('keyInformation')}")
