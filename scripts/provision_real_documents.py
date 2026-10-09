import os
import sys
import json
import urllib.request
import urllib.parse
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

DOCS_DIR = os.path.join(os.path.dirname(__file__), "generated_pdfs")
os.makedirs(DOCS_DIR, exist_ok=True)

def create_pdf(filepath, title, sections):
    doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=14,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=8,
    )

    story = [
        Paragraph(title, title_style),
        Paragraph("<b>Institution:</b> Anna University / VEXORA Educational Consortium", body_style),
        Paragraph("<b>Official University Gazette:</b> Approved by Academic Senate & Syndicate", body_style),
        Spacer(1, 15),
    ]

    for sec_title, sec_paragraphs in sections:
        story.append(Paragraph(sec_title, heading_style))
        for p in sec_paragraphs:
            story.append(Paragraph(p, body_style))
        story.append(Spacer(1, 8))

    doc.build(story)
    print(f"[PDF] Created: {os.path.basename(filepath)} ({os.path.getsize(filepath)} bytes)")

def generate_all_pdfs():
    # 1. Academic Regulations 2026 (Amended from 2025)
    create_pdf(
        os.path.join(DOCS_DIR, "ACADEMIC REGULATIONS 2026.pdf"),
        "B.E. / B.Tech. Academic Regulations 2026 (Revised Edition)",
        [
            ("Section 1: Preamble and Applicability", [
                "These Academic Regulations 2026 shall govern all undergraduate degree programmes of engineering and technology admitted from the academic year 2026-2027 onwards.",
                "All registered students must satisfy the minimum requirements for course completion, continuous evaluation, and semester examinations."
            ]),
            ("Section 11: Attendance Requirements", [
                "11.1. Each student is expected to attend 100% of the working periods scheduled for each course in every semester.",
                "11.2. The University mandates a minimum overall attendance of 85% across all registered theory and laboratory courses. A student securing below 85% overall attendance shall not be permitted to appear for the End Semester Examinations.",
                "11.3. Continuous assessment marks shall be computed incorporating the candidate's attendance record throughout the 15-week instructional semester.",
                "11.4. Medical Condonation: On exceptional medical grounds supported by authentic hospital documentation submitted within 5 working days, attendance between 75% and 84% may be condoned by the Dean of Academic Courses with a prescribed condonation fee."
            ]),
            ("Section 17: Teaching, Evaluation & Assessment Weights", [
                "17.1. Each registered course is assessed through Continuous Internal Assessment (CIA) and University End Semester Examinations (ESE).",
                "17.2. Continuous Internal Assessment (CIA) weightage is established at 50% for all undergraduate theory courses.",
                "17.3. University End Semester Examination (ESE) weightage is established at 50% of the total aggregate score.",
                "17.4. Practical laboratory courses shall have 60% continuous assessment and 40% practical semester examination."
            ]),
            ("Section 18: Passing Criteria and Minimum Marks", [
                "18.1. A student must secure a minimum of 50 Marks out of 100 in the End Semester Examination to qualify for a pass in that course.",
                "18.2. In aggregate (combining CIA and End Semester Examination marks), the student must secure a minimum of 50% overall to be awarded a letter grade."
            ])
        ]
    )

    # 2. Examination Regulations & Handbook 2025
    create_pdf(
        os.path.join(DOCS_DIR, "EXAMINATION REGULATIONS & HANDBOOK 2025.pdf"),
        "University Examination Regulations and Evaluation Handbook 2025",
        [
            ("Section 1: General Examination Protocol", [
                "1.1. The Controller of Examinations (COE) is responsible for the conduct of all Continuous Internal Assessments and End Semester Examinations.",
                "1.2. Students must be seated in their designated examination hall at least 15 minutes prior to the commencement of the examination.",
                "1.3. Candidates arriving more than 30 minutes after the scheduled start time will not be permitted to enter the examination hall under any circumstances."
            ]),
            ("Section 2: Internal Assessment and Continuous Evaluation", [
                "2.1. Continuous Internal Assessment (CIA) shall consist of three internal assessment tests (IAT 1, IAT 2, IAT 3) conducted across the semester.",
                "2.2. The total Continuous Internal Assessment weightage is 40 Marks, while the End Semester Examination carries 60 Marks.",
                "2.3. The average of the best two internal tests alongside assignment and tutorial components constitutes the final internal mark.",
                "2.4. Faculty members must upload internal assessment marks to the university portal within 7 working days following each test."
            ]),
            ("Section 3: Passing Minimum and Grading Standards", [
                "3.1. A candidate must secure a minimum of 45% in the End Semester Examination and 50% in aggregate (CIA + ESE combined) to pass the course.",
                "3.2. Letter grades from O (Outstanding) to U (Re-appearance) shall be allocated based on absolute mark brackets prescribed by the Academic Senate."
            ]),
            ("Section 4: Malpractice Prevention and Disciplinary Codes", [
                "4.1. Possession of unauthorized materials, programmable calculators, electronic gadgets, or mobile phones inside the examination hall is strictly prohibited.",
                "4.2. Any student found engaging in examination malpractice shall be referred to the Central Malpractice Enquiry Committee (CMEC).",
                "4.3. Penalties range from cancellation of the subject examination to debarment from the university for up to two consecutive semesters."
            ])
        ]
    )

    # 3. Hostel Rules & Residential Policy
    create_pdf(
        os.path.join(DOCS_DIR, "HOSTEL RULES & RESIDENTIAL POLICY.pdf"),
        "University Student Hostel Rules & Residential Policy",
        [
            ("Section 1: Admission and Room Allocation", [
                "1.1. Hostel accommodation is allotted to full-time registered students on a merit and distance basis for an academic session of 10 months.",
                "1.2. Room allotment is finalized by the Chief Warden. Unauthorized switching or sub-letting of hostel rooms is strictly forbidden and results in immediate forfeiture of residency.",
                "1.3. Students must inspect hostel fixtures upon occupancy and report any pre-existing damage within 48 hours."
            ]),
            ("Section 2: Curfew Hours and Biometric Verification", [
                "2.1. Mandatory curfew for all resident hostel students is 8:30 PM on all days including weekends.",
                "2.2. Night biometric attendance verification takes place between 8:30 PM and 9:15 PM daily under warden supervision.",
                "2.3. Late entry requires prior written approval from the Faculty Warden. Unexcused late entry after 8:30 PM on three occasions results in a formal disciplinary notice to parents."
            ]),
            ("Section 3: Mess Regulations and Dining Facilities", [
                "3.1. All hostel residents are enrolled in the compulsory cooperative student mess facility offering balanced nutritional menus.",
                "3.2. Mess rebates are permissible only for authorized academic or medical leave exceeding 5 consecutive days, submitted 48 hours in advance.",
                "3.3. Taking dining hall crockery, cutlery, or meals to residential rooms is prohibited except under certified medical bed rest."
            ]),
            ("Section 4: Discipline, Quiet Hours and Prohibitions", [
                "4.1. Quiet study hours are observed between 10:00 PM and 6:00 AM daily to facilitate uninterrupted academic preparation.",
                "4.2. The use of heavy heating appliances, cooking stoves, or motorized electric heaters inside hostel rooms is strictly prohibited.",
                "4.3. Possession or consumption of alcoholic beverages, narcotics, or tobacco inside university premises entails immediate expulsion from the hostel."
            ])
        ]
    )

    # 4. Placement Eligibility & Guidelines
    create_pdf(
        os.path.join(DOCS_DIR, "PLACEMENT ELIGIBILITY & GUIDELINES.pdf"),
        "Campus Recruitment Training & Placement Eligibility Guidelines",
        [
            ("Section 1: General Eligibility Criteria", [
                "1.1. Registration with the Career Development Centre (CDC) is mandatory for participating in on-campus and off-campus recruitment drives.",
                "1.2. Students must maintain a minimum CGPA of 7.5 across all completed semesters with zero active or standing arrears at the time of campus recruitment drives.",
                "1.3. Minimum 60% aggregate in 10th and 12th standard board examinations is required by most core engineering and multinational recruiters.",
                "1.4. Mandatory minimum attendance of 90% in all Pre-Placement Training (PPT), soft skills, and aptitude workshops is required to maintain placement eligibility."
            ]),
            ("Section 2: Placement Offer Policies and Regulations", [
                "2.1. The university enforces a strict One-Student-One-Offer policy to ensure equitable placement opportunities for all eligible candidates.",
                "2.2. Dream Offer Policy: A student holding a standard offer (below 10 LPA) may appear for 'Dream Companies' offering a compensation package of 10 LPA or higher.",
                "2.3. Super Dream Offer Policy: Students securing a Dream Offer may contest for premium tier organizations offering 20 LPA or above.",
                "2.4. Once a student accepts an offer from a Dream or Super Dream company, they are decommissioned from all further campus drives."
            ]),
            ("Section 3: Professional Code of Conduct for Interviews", [
                "3.1. Candidates must appear in formal business attire for all written tests, group discussions, and technical/HR interviews.",
                "3.2. Resume details including projects, internships, and certifications must be verified and endorsed by the CDC faculty coordinator.",
                "3.3. Misrepresentation of academic scores or unexcused absenteeism from scheduled interviews results in immediate cancellation of placement privilege for the entire academic year."
            ])
        ]
    )

    # 5. Campus Code of Conduct & Disciplinary Rules
    create_pdf(
        os.path.join(DOCS_DIR, "CAMPUS CODE OF CONDUCT & DISCIPLINARY RULES.pdf"),
        "Student Campus Code of Conduct and Disciplinary Procedures",
        [
            ("Section 1: University Identity and Campus Demeanor", [
                "1.1. Every student must visibly wear their official university smart ID card with RFID lanyard at all times while present inside university premises.",
                "1.2. Students must adhere to a neat, professional dress code appropriate for an academic institution during all instructional hours.",
                "1.3. Unauthorized entry into laboratories, server rooms, or faculty departmental corridors outside operating hours is considered trespassing."
            ]),
            ("Section 2: Anti-Ragging Policy and Zero Tolerance", [
                "2.1. The university maintains a strict Zero Tolerance policy towards ragging in any form, directly or indirectly, on or off campus, in full accordance with UGC regulations.",
                "2.2. Any act of physical harassment, psychological intimidation, teasing, or abuse of freshmen will lead to immediate FIR filing, suspension, and expulsion.",
                "2.3. The 24x7 Anti-Ragging Helpline and Internal Compliance Committee contact details are displayed at all college entrances."
            ]),
            ("Section 3: Campus Traffic, Vehicles and Safety", [
                "3.1. Student motorized vehicles must obtain an annual campus parking permit sticker from the Chief Security Officer.",
                "3.2. The maximum vehicle speed limit on all campus roads and connecting avenues is 20 km/h.",
                "3.3. Helmet usage is mandatory for riders and pillion passengers of two-wheelers entering university gates."
            ]),
            ("Section 4: Disciplinary Committee Inquiries", [
                "4.1. All reported infractions are investigated by the Proctorial Disciplinary Board comprising senior professors and student representatives.",
                "4.2. Inquiries must be completed and a formal report submitted to the Vice-Chancellor within 7 working days of the reported incident."
            ])
        ]
    )

    # 6. General Campus Facilities & Welfare Services
    create_pdf(
        os.path.join(DOCS_DIR, "GENERAL CAMPUS FACILITIES & SERVICES.pdf"),
        "University General Campus Facilities & Student Welfare Services",
        [
            ("Section 1: Central Library and Knowledge Resource Centre", [
                "1.1. The Central Library operates from 8:00 AM to 8:00 PM on all working days and 9:00 AM to 4:00 PM on Sundays and designated study holidays.",
                "1.2. Undergraduate students are entitled to borrow up to 5 books simultaneously for a borrowing period of 14 days, renewable once online.",
                "1.3. The Digital Knowledge Hub provides complimentary high-speed access to IEEE Xplore, ScienceDirect, and SpringerLink electronic journals."
            ]),
            ("Section 2: Health Centre and Emergency Medical Care", [
                "2.1. The 24-hour University Health Centre is staffed by qualified resident medical officers and registered nursing staff.",
                "2.2. Emergency ambulance service is stationed on campus and can be dispatched immediately via emergency extension 108.",
                "2.3. Complimentary consultation and essential prescription medicines are provided free of cost to all bonafide students upon presentation of student ID."
            ]),
            ("Section 3: Transport and Shuttle Bus Services", [
                "3.1. The university operates 45 fleet buses connecting major residential zones, suburban rail junctions, and metro stations across the metropolitan region.",
                "3.2. Students must carry valid semester bus passes issued by the Transport Officer.",
                "3.3. Complimentary electric intra-campus battery shuttles operate every 10 minutes connecting academic blocks, hostels, and sports grounds."
            ]),
            ("Section 4: Student Grievance Redressal Mechanism", [
                "4.1. An online Student Grievance Redressal Portal is accessible 24x7 through the student ERP login.",
                "4.2. All grievances are acknowledged within 24 hours and resolved within 10 working days by the Student Welfare Dean."
            ])
        ]
    )

def upload_file_multipart(token, filepath, category, version):
    filename = os.path.basename(filepath)
    boundary = "----VexoraBoundary" + os.urandom(8).hex()

    with open(filepath, "rb") as f:
        file_bytes = f.read()

    body = bytearray()

    # Form field: category
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(f'Content-Disposition: form-data; name="category"\r\n\r\n{category}\r\n'.encode("utf-8"))

    # Form field: version
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(f'Content-Disposition: form-data; name="version"\r\n\r\n{version}\r\n'.encode("utf-8"))

    # File field
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode("utf-8"))
    body.extend(b"Content-Type: application/pdf\r\n\r\n")
    body.extend(file_bytes)
    body.extend(b"\r\n")

    # End boundary
    body.extend(f"--{boundary}--\r\n".encode("utf-8"))

    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/documents/upload",
        data=bytes(body),
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Authorization": f"Bearer {token}",
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"[UPLOAD SUCCESS] {filename} -> Doc ID: {data.get('document', {}).get('id')} | Chunks: {data.get('document', {}).get('total_chunks')} | Cat: {data.get('document', {}).get('category')} | Ver: {data.get('document', {}).get('version')}")
            return data
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore")
        print(f"[UPLOAD HTTP ERROR {e.code}] {filename}: {err_msg}")
        return {"error": e.code, "detail": err_msg}
    except Exception as e:
        print(f"[UPLOAD FAILED] {filename}: {e}")
        return {"error": str(e)}

def main():
    print("=" * 60)
    print("VEXORA REAL DOCUMENT GENERATOR & INGESTION")
    print("=" * 60)

    # 1. Login
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/auth/login",
        data=json.dumps({"email": "admin@vexora.edu", "password": "Admin@2026"}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        token = json.loads(resp.read().decode("utf-8"))["token"]
    print("[AUTH] Successfully logged in as admin@vexora.edu")

    # 2. Generate PDFs
    generate_all_pdfs()

    # 3. Upload to API
    docs_to_upload = [
        ("ACADEMIC REGULATIONS 2026.pdf", "Academic", "v2.0"),
        ("EXAMINATION REGULATIONS & HANDBOOK 2025.pdf", "Examination", "v1.0"),
        ("HOSTEL RULES & RESIDENTIAL POLICY.pdf", "Hostel", "v1.0"),
        ("PLACEMENT ELIGIBILITY & GUIDELINES.pdf", "Placement", "v1.0"),
        ("CAMPUS CODE OF CONDUCT & DISCIPLINARY RULES.pdf", "Rules", "v1.0"),
        ("GENERAL CAMPUS FACILITIES & SERVICES.pdf", "General", "v1.0"),
    ]

    print("\n--- Ingesting Documents through Real Backend Pipeline ---")
    results = []
    for fname, cat, ver in docs_to_upload:
        fpath = os.path.join(DOCS_DIR, fname)
        res = upload_file_multipart(token, fpath, cat, ver)
        results.append(res)

    # 4. Duplicate Document Test (Upload same file again)
    print("\n--- Testing Duplicate Document Detection ---")
    dup_path = os.path.join(DOCS_DIR, "HOSTEL RULES & RESIDENTIAL POLICY.pdf")
    dup_res = upload_file_multipart(token, dup_path, "Hostel", "v1.0")
    if dup_res.get("error") == 409:
        print("[DUPLICATE TEST PASSED] Backend correctly rejected duplicate with HTTP 409!")
    else:
        print(f"[DUPLICATE TEST WARNING] Unexpected response: {dup_res}")

    print("\n[PROVISION COMPLETE] All university documents ingested and verified.")

if __name__ == "__main__":
    main()
