import urllib.request
import json
import os

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/auth/login',
    data=json.dumps({'email': 'admin@vexora.edu', 'password': 'Admin@2026'}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
with urllib.request.urlopen(req) as resp:
    token = json.loads(resp.read().decode('utf-8'))['token']

# 1. Create a temporary text file to upload
test_file = "temp_to_delete.txt"
with open(test_file, "w") as f:
    f.write("Section 1: General University Campus Guidelines and Deletion Verification Protocol.\n\n"
            "This official university policy document is published for verification purposes. "
            "All registered undergraduate and postgraduate students shall adhere to the statutory guidelines "
            "promulgated by the university senate. Violations of these temporary administrative provisions "
            "will be subject to inquiry by the campus disciplinary committee within fourteen working days.")

boundary = "----VexoraBoundary" + os.urandom(8).hex()
body = bytearray()
body.extend(f"--{boundary}\r\n".encode("utf-8"))
body.extend(b'Content-Disposition: form-data; name="category"\r\n\r\nGeneral\r\n')
body.extend(f"--{boundary}\r\n".encode("utf-8"))
body.extend(b'Content-Disposition: form-data; name="version"\r\n\r\nv1.0\r\n')
body.extend(f"--{boundary}\r\n".encode("utf-8"))
body.extend(f'Content-Disposition: form-data; name="file"; filename="{test_file}"\r\n'.encode("utf-8"))
body.extend(b"Content-Type: text/plain\r\n\r\n")
with open(test_file, "rb") as f:
    body.extend(f.read())
body.extend(b"\r\n")
body.extend(f"--{boundary}--\r\n".encode("utf-8"))

upload_req = urllib.request.Request(
    "http://127.0.0.1:8000/api/documents/upload",
    data=bytes(body),
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}", "Authorization": f"Bearer {token}"},
    method="POST"
)

with urllib.request.urlopen(upload_req) as resp:
    up_data = json.loads(resp.read().decode("utf-8"))
    doc_id = up_data["document"]["id"]
    print(f"[TEST UPLOAD] Uploaded temp doc with ID: {doc_id}")

os.remove(test_file)

# 2. Verify it exists
check_req = urllib.request.Request(f"http://127.0.0.1:8000/api/documents/{doc_id}", headers={"Authorization": f"Bearer {token}"})
with urllib.request.urlopen(check_req) as resp:
    print(f"[VERIFY] Document exists before delete: HTTP {resp.status}")

# 3. Delete it
del_req = urllib.request.Request(f"http://127.0.0.1:8000/api/documents/{doc_id}", headers={"Authorization": f"Bearer {token}"}, method="DELETE")
with urllib.request.urlopen(del_req) as resp:
    print(f"[DELETE] Delete request response: HTTP {resp.status}")

# 4. Verify it's gone
try:
    check_again = urllib.request.Request(f"http://127.0.0.1:8000/api/documents/{doc_id}", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(check_again) as resp:
        print("[WARNING] Document still exists!")
except urllib.error.HTTPError as e:
    if e.code == 404:
        print("[DELETE TEST PASSED] Document is confirmed 404 Not Found after deletion!")
    else:
        print(f"[DELETE TEST ERROR] Unexpected status: {e.code}")
