import streamlit as st
import pdfplumber
import re
from collections import defaultdict
from datetime import datetime

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
        "search_terms": ["Runway Incursion", "Runway Incursion Exam"],
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
        "search_terms": ["TCAS II ", "Traffic Collision Avoidance System (TCASII)", "TCAS II - Exam"],
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
        "search_terms": ["The Helicopter and Jet Company - SMS", "THC - SMS Exam", "SMS Exam"],
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

def clean_text(text):
    # Fix common OCR errors in dates, e.g., "202 2024" -> "2024"
    text = re.sub(r'(\d{3})\s+(\d{4})', lambda m: m.group(2) if m.group(2).startswith(m.group(1)) else m.group(0), text)
    return text

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
    return clean_text(text)

month_pattern = re.compile(r'(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', re.I)

date_pattern = re.compile(r'(\d{1,2}\s*-\s*[a-z]{3}\s*-\s*\d{4})|(\d{4}\s*-\s*[a-z]{3}\s*-\s*\d{1,2})', re.I)

def parse_date(date_str):
    if not date_str:
        return None
    date_str = date_str.replace(' ', '')  # Remove spaces
    formats = ['%d-%b-%Y', '%Y-%b-%d']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            pass
    return None

def parse_completed_subjects(text):
    text_lower = text.lower()
    is_super_condensed = "super condensed report by student" in text_lower
    lines = text.split('\n')
    subjects_sections = defaultdict(list)
    current_subject = None
    for line in lines:
        line_lower = line.lower()
        found = False
        for sub, data in subjects.items():
            for term in data["search_terms"]:
                if term.lower() in line_lower:
                    current_subject = sub
                    found = True
                    break
            if found:
                break
        if current_subject:
            subjects_sections[current_subject].append(line)
    completed = {}
    for subject, section in subjects_sections.items():
        section_text = '\n'.join(section).lower()
        # Base month
        base_month = None
        base_match = re.search(r'base month\s*[:\s*](\w+)', section_text, re.I)
        if base_match:
            base_month = base_match.group(1).capitalize()
        else:
            early_text = ' '.join(section[:3]).lower()
            no_date_early = date_pattern.sub('', early_text)
            month_match = month_pattern.search(no_date_early)
            if month_match:
                base_month = month_match.group(0).capitalize()
        # Look for exam score and date
        exam_status = 'PASS'
        exam_score = None
        exam_date = None
        found_exam = False
        for i, line in enumerate(section):
            line_clean = line.replace('$', '').lower()
            if re.search(r'\bexam\b', line_clean):
                found_exam = True
                score_found = False
                for m in range(0, 7):
                    if i + m < len(section):
                        sub_line = section[i + m]
                        sub_line_clean = sub_line.replace('$', '').lower()
                        score_match = re.search(r'(\d+)\s*%\s*(pass|fail)?', sub_line_clean)
                        if score_match:
                            score_num = score_match.group(1)
                            exam_score = score_num + '%'
                            status_str = score_match.group(2) or ''
                            exam_status = 'PASS' if 'pass' in status_str.lower() or int(score_num) >= 70 else 'FAIL'
                            score_found = True
                            # Find date
                            date_match = date_pattern.search(sub_line)
                            if date_match:
                                exam_date = date_match.group(0)
                            else:
                                for p in range(-3, 7):
                                    q = i + m + p
                                    if 0 <= q < len(section):
                                        date_match = date_pattern.search(section[q])
                                        if date_match:
                                            exam_date = date_match.group(0)
                                            break
                            break
                if score_found:
                    break
        if found_exam and exam_score:
            completed[subject] = (exam_status, exam_score, base_month, exam_date)
        elif is_super_condensed:
            # Fallback for super condensed
            exam_status = 'PASS'
            exam_score = '100%'
            # Find last date in section
            section_str = '\n'.join(section)
            dates = [d for group in date_pattern.findall(section_str) for d in group if d]
            if dates:
                exam_date = dates[-1]
            completed[subject] = (exam_status, exam_score, base_month, exam_date)

    return completed

def get_color(status_or_perc):
    if isinstance(status_or_perc, str):
        return GREEN if 'PASS' in status_or_perc else RED
    else:
        if status_or_perc == 100:
            return GREEN
        else:
            return YELLOW

def generate_table(completed):
    output = "<table><thead><tr><th>Subject</th><th>Status</th><th>Score</th><th>Base Month</th><th>Date</th></tr></thead><tbody>"
    for subject, (status, score, base_month, date) in sorted(completed.items()):
        base_str = base_month or 'N/A'
        score_str = score or 'N/A'
        date_str = date or 'N/A'
        color = get_color(status)
        status_colored = f"{color}{status}{RESET}"
        output += f"<tr><td>{subject}</td><td>{status_colored}</td><td>{score_str}</td><td>{base_str}</td><td>{date_str}</td></tr>"
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
            perc = details['completion_percentage']
            date_info = ""
            if perc == 100:
                dates = []
                for sub in courses[name]:
                    if sub in completed and completed[sub][0] == 'PASS' and completed[sub][3]:
                        parsed_date = parse_date(completed[sub][3])
                        if parsed_date:
                            dates.append(parsed_date)
                if dates:
                    start_date = min(dates).strftime('%d-%b-%Y')
                    end_date = max(dates).strftime('%d-%b-%Y')
                    date_info = f" - Start: {start_date}, End: {end_date}"
            output += f"<p><strong>{name}: {perc:.0f}%{date_info}</strong></p><ul>"
            all_subs = courses[name]
            for sub in sorted(all_subs):
                if sub in completed:
                    status, score, base_mo, date = completed[sub]
                    color = get_color(status)
                    base_str = base_mo or 'N/A'
                    score_str = score or 'N/A'
                    output += f"<li>{color}+ {sub} - {status} {score_str} {base_str}{RESET}</li>"
                else:
                    output += f"<li>{RED}- {sub}{RESET}</li>"
            output += "</ul>"
    return output

def analyze_courses(completed):
    results = {}
    for course_name, req_subjects in courses.items():
        total = len(req_subjects)
        completed_count = sum(1 for sub in req_subjects if sub in completed and completed[sub][0] == 'PASS')
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
