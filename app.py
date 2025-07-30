import streamlit as st
import pdfplumber
import re
from collections import defaultdict

# HTML color spans
GREEN = '<span style="color:green">'
RED = '<span style="color:red">'
YELLOW = '<span style="color:orange">'  # Orange for better visibility than yellow
RESET = '</span>'

# Subjects dict (with all your added search terms)
subjects = {
    "ADS-B": {
        "search_terms": ["ADS-B Overview", "ADS-B Exam"],
        "courses": ["Initial General Subjects Course", "Module 1"]
    },
    "Weather": {
        "search_terms": ["Aviation Weather Theory", "Aviation Weather Theory Exam"],
        "courses": ["Initial General Subjects Course", "Module 1"]
    },
    "Aerodynamics": {
        "search_terms": ["Helicopter Aerodynamics", "Helicopter Specific Exam"],
        "courses": ["Initial General Subjects Course", "Module 1"]
    },
    "Airspace": {
        "search_terms": ["Airspace Overview", "Airspace Overview Exam"],
        "courses": ["Initial General Subjects Course", "Module 1"]
    },
    "Brownout": {
        "search_terms": ["Flat-light, Whiteout, and Brownout Conditions"],
        "courses": ["Initial General Subjects Course", "Module 1"]
    },
    "CFIT": {
        "search_terms": ["Controlled Flight into Terrain Avoidance (CFIT, TAWS, and ALAR) - RW", "Controlled Flight into Terrain Avoidance RW Exam"],
        "courses": ["Initial General Subjects Course", "Module 1"]
    },
    "Fire Classes": {
        "search_terms": ["Classes of Fire and Portable Fire Extinguishers", "Portable Fire Extinguisher Exam"],
        "courses": ["Initial General Subjects Course", "Module 1"]
    },
    "GPS": {
        "search_terms": ["GPS (RW IFR-VFR)", "GPS (RW IFR) Exam"],
        "courses": ["Initial General Subjects Course", "Module 1"]
    },
    "External Lighting": {
        "search_terms": ["Helicopter External Lighting", "Helicopter External Lighting Exam"],
        "courses": ["Initial General Subjects Course", "Module 2"]
    },
    "METAR and TAF": {
        "search_terms": ["METAR and TAF", "METAR and TAF Exam"],
        "courses": ["Initial General Subjects Course", "Module 2"]
    },
    "First Aid": {
        "search_terms": ["Physiology and First Aid (RW)", "Physiology and First Aid (RW) Exam"],
        "courses": ["Initial General Subjects Course", "Module 2"]
    },
    "Runway Incursion": {
        "search_terms": ["Survival", "Runway Incursion Exam"],
        "courses": ["Initial General Subjects Course", "Module 2"]
    },
    "Survival": {
        "search_terms": ["Survival", "Survival Exam"],
        "courses": ["Initial General Subjects Course", "Module 2"]
    },
    "Traffic Advisory System": {
        "search_terms": ["Traffic Advisory System (TAS)", "Traffic Advisory System"],
        "courses": ["Initial General Subjects Course", "Module 2"]
    },
    "Traffic Collision Avoidance System": {
        "search_terms": ["Traffic Collision Avoidance System (TCASII)", "TCAS II - Exam"],
        "courses": ["Initial General Subjects Course", "Module 2"]
    },
    "Windshear": {
        "search_terms": ["Windshear (RW)", "Helicopter Windshear Exam"],
        "courses": ["Initial General Subjects Course", "Module 2"]
    },
    "Wire Strike Prevention": {
        "search_terms": ["Wire Strike Prevention", "Wire Strike Prevention Exam"],
        "courses": ["Wire Strike Prevention"]
    },
    "Basic Indoc": {
        "search_terms": ["The Helicopter and Jet Company - Indoc (NEW)", "The Helicopter Company - Indoc - SUPERCEDED", "THC - Indoc - EXAM"],
        "courses": ["Basic Indoc"]
    },
    "SMS": {
        "search_terms": ["The Helicopter and Jet Company - SMS", "THC - SMS Exam"],
        "courses": ["SMS"]
    },
    "Hazmat": {
        "search_terms": ["Hazmat - Will Not Carry", "Hazmat Will Not Carry Exam"],
        "courses": ["Dangerous Goods"]
    },
    "CRM": {
        "search_terms": ["CRM-ADM - Rotor Wing", "Crew Resource Management - Rotor Wing Exam"],
        "courses": ["CRM"]
    },
    "AW139": {
        "search_terms": ["AW-139", "AW-139 Examination"],
        "courses": ["AW139"]
    },
    "H145": {
        "search_terms": ["H145 (EC-145T2)"],
        "courses": ["H145"]
    },
}

# Threshold for "likely" course match (in %)
LIKELY_THRESHOLD = 70

# Dynamically build courses dict from subjects
courses = defaultdict(set)
for subject, data in subjects.items():
    for course in data["courses"]:
        courses[course].add(subject)

def extract_text_from_pdf(pdf_file):
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        st.error(f"Error extracting text: {e}")
    return text

def parse_completed_subjects(text):
    completed = defaultdict(list)  # subject -> list of (date, status, score, base_month)

    text_lower = text.lower()
    lines = text.split('\n')

    for i, line in enumerate(lines):
        line_lower = line.lower()
        for subject, data in subjects.items():
            for term in data["search_terms"]:
                term_lower = term.lower()
                if term_lower in line_lower:
                    start = max(0, i - 10)
                    end = min(len(lines), i + 50)
                    context = ' '.join(lines[start:end]).lower()
                    context_lines = lines[start:end]

                    base_month_match = re.search(r'base month\s*[:|]\s*(\w+)', context, re.I)
                    base_month = base_month_match.group(1).capitalize() if base_month_match else None

                    exam_date = None
                    exam_status = 'PASS'
                    exam_score = None
                    for ctx_line in context_lines:
                        exam_match = re.search(r'exam\s*(\d+%)\s*(pass|fail)?\s*(\d{4}-[a-z]{3}-\d{1,2}|\d{2}-[a-z]{3}-\d{4}|\d{4}-\d{2}-\d{2})', ctx_line.lower())
                        if exam_match:
                            exam_score = exam_match.group(1).upper()
                            status_str = exam_match.group(2) or ''
                            exam_status = 'PASS' if 'pass' in status_str or int(exam_score.rstrip('%')) >= 70 else 'FAIL'
                            exam_date = exam_match.group(3)
                            break

                    fallback_date = None
                    if not exam_date:
                        date_patterns = [
                            r'\d{4}-[a-z]{3}-\d{1,2}',
                            r'\d{2}-[a-z]{3}-\d{4}',
                            r'\d{4}-\d{2}-\d{2}',
                        ]
                        for pattern in date_patterns:
                            date_match = re.search(pattern, context)
                            if date_match:
                                fallback_date = date_match.group(0)
                                break

                    date = exam_date or fallback_date

                    if exam_score is None:
                        status_match = re.search(r'(\d+%)\s*(pass|fail)?', context)
                        if status_match:
                            exam_score = status_match.group(1).upper()
                            status_str = status_match.group(2) or ''
                            exam_status = 'PASS' if 'pass' in status_str or int(exam_score.rstrip('%')) >= 70 else 'FAIL'
                        else:
                            exam_status = 'PASS' if 'pass' in context else ('FAIL' if 'fail' in context else 'PASS')

                    completed[subject].append((date, exam_status, exam_score, base_month))
                    break

    unique_completed = {}
    for subject, entries in completed.items():
        sorted_entries = sorted(entries, key=lambda x: (x[2] is not None, x[0] is not None, x[3] is not None, x[1] == 'PASS'), reverse=True)
        unique_completed[subject] = sorted_entries[0]

    return unique_completed

def get_color(status_or_perc):
    if isinstance(status_or_perc, str):
        return GREEN if 'PASS' in status_or_perc else RED
    else:
        if status_or_perc >= 90:
            return GREEN
        elif status_or_perc >= 50:
            return YELLOW
        else:
            return RED

def generate_table(completed):
    output = "<table><thead><tr><th>Subject</th><th>Date</th><th>Status</th><th>Score</th><th>Base Mo</th></tr></thead><tbody>"
    for subject, (date, status, score, base_mo) in sorted(completed.items()):
        date_str = date or 'Unknown'
        base_str = base_mo or 'N/A'
        score_str = score or 'N/A'
        color = get_color(status)
        status_colored = f"{color}{status}{RESET}"
        output += f"<tr><td>{subject}</td><td>{date_str}</td><td>{status_colored}</td><td>{score_str}</td><td>{base_str}</td></tr>"
    output += "</tbody></table>"
    return output

def generate_courses(results, completed):
    sorted_results = sorted(results.items(), key=lambda x: x[1]['completion_percentage'], reverse=True)
    output = "<h3>Likely Lists:</h3><ul>"
    for name, details in sorted_results:
        perc = details['completion_percentage']
        color = get_color(perc)
        output += f"<li>{name}: {color}{perc:.0f}%{RESET}</li>"
    output += "</ul><h3>List Details:</h3>"
    for name, details in sorted_results:
        if details['completion_percentage'] > 0:
            output += f"<p><strong>{name}: {details['completion_percentage']:.0f}%</strong></p><ul>"
            all_subs = courses[name]
            for sub in sorted(all_subs):
                if sub in completed:
                    date, status, score, base_mo = completed[sub]
                    color = get_color(status)
                    date_str = date or 'Unknown'
                    base_str = base_mo or 'N/A'
                    score_str = score or 'N/A'
                    output += f"<li>{color}+ {sub} - {date_str} {status} {score_str} {base_str}{RESET}</li>"
                else:
                    output += f"<li>{RED}- {sub}{RESET}</li>"
            output += "</ul>"
    return output

def analyze_courses(completed):
    results = {}
    for course_name, req_subjects in courses.items():
        total = len(req_subjects)
        completed_count = sum(1 for sub in req_subjects if sub in completed and completed[sub][1] == 'PASS')
        results[course_name] = {'completion_percentage': (completed_count / total * 100) if total else 0}
    return results

# Streamlit app
st.title("PDF Exam Analyzer")
st.markdown("**Instructions:** Drag and drop your PDF into the box below (or click 'Browse files' to select). Then click 'Process PDF'. Do NOT drop the PDF on the full page—it will open the file instead.")
uploaded_file = st.file_uploader("Upload PDF", type="pdf")

if uploaded_file is not None:
    if st.button("Process PDF"):
        text = extract_text_from_pdf(uploaded_file)
        if not text:
            st.error("No text extracted from PDF. The file may be scanned/image-only or corrupted.")
        else:
            completed = parse_completed_subjects(text)
            if completed:
                st.subheader("Subjects Detected")
                st.markdown(generate_table(completed), unsafe_allow_html=True)
                results = analyze_courses(completed)
                st.markdown(generate_courses(results, completed), unsafe_allow_html=True)
            else:
                st.warning("No subjects detected in the PDF.")
