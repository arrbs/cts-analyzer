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
    completed = defaultdict(list)  # subject -> list of (status, score, base_month, date)

    text_lower = text.lower()
    lines = text.split('\n')

    date_pattern = re.compile(r'(\d{4}-[a-z]{3}-\d{1,2})|(\d{1,2}/\d{1,2}/\d{4})', re.I)  # Matches YYYY-Mmm-DD or MM/DD/YYYY

    for i, line in enumerate(lines):
        line_lower = line.lower()
        for subject, data in subjects.items():
            for term in data["search_terms"]:
                term_lower = term.lower()
                if term_lower in line_lower:
                    start = max(0, i - 10)  # Backward for base month
                    end = min(len(lines), i + 50)
                    context = ' '.join(lines[start:end]).lower()
                    context_lines = lines[start:end]

                    base_month_match = re.search(r'base month\s*[:|]\s*(\w+)', context, re.I)
                    base_month = base_month_match.group(1).capitalize() if base_month_match else None

                    # Calculate offset to start from the matched line
                    offset = i - start

                    exam_status = 'PASS'
                    exam_score = None
                    exam_date = None
                    for j, ctx_line in enumerate(context_lines[offset:], start=offset):
                        # Strip potential OCR artifacts like '$'
                        ctx_line_clean = ctx_line.replace('$', '').lower()
                        exam_match = re.search(r'exam\s*(\d+%)\s*(pass|fail)?', ctx_line_clean)
                        if exam_match:
                            exam_score = exam_match.group(1).upper()
                            status_str = exam_match.group(2) or ''
                            exam_status = 'PASS' if 'pass' in status_str or int(exam_score.rstrip('%')) >= 70 else 'FAIL'
                            
                            # Look for date on this line, prev, or next (extended to j+3)
                            for k in range(max(0, j-1), min(len(context_lines), j+3)):
                                date_match = date_pattern.search(context_lines[k])
                                if date_match:
                                    exam_date = date_match.group(0)
                                    break
                            if exam_date:
                                break  # Stop once we have score and date

                    if exam_score is None:
                        # Fallback: loop to find line with score, then date near it
                        for j, ctx_line in enumerate(context_lines[offset:], start=offset):
                            ctx_line_clean = ctx_line.replace('$', '').lower()
                            status_match = re.search(r'(\d+%)\s*(pass|fail)?', ctx_line_clean)
                            if status_match:
                                exam_score = status_match.group(1).upper()
                                status_str = status_match.group(2) or ''
                                exam_status = 'PASS' if 'pass' in status_str or int(exam_score.rstrip('%')) >= 70 else 'FAIL'
                                
                                # Look for date near this line (extended to j+3)
                                for k in range(max(0, j-1), min(len(context_lines), j+3)):
                                    date_match = date_pattern.search(context_lines[k])
                                    if date_match:
                                        exam_date = date_match.group(0)
                                        break
                                if exam_date:
                                    break  # Stop once we have score and date

                        if exam_score is None:
                            # New fallback for "Complete" without score
                            for j, ctx_line in enumerate(context_lines[offset:], start=offset):
                                ctx_line_clean = ctx_line.lower()
                                if 'complete' in ctx_line_clean:
                                    exam_status = 'PASS'
                                    exam_score = None
                                    
                                    # Look for date near this line
                                    for k in range(max(0, j-1), min(len(context_lines), j+3)):
                                        date_match = date_pattern.search(context_lines[k])
                                        if date_match:
                                            exam_date = date_match.group(0)
                                            break
                                    if exam_date:
                                        break  # Stop once we have date
                            
                            if exam_status == 'PASS' and not exam_date:
                                # If found complete but no date, search forward
                                for k in range(offset, min(len(context_lines), offset+5)):
                                    date_match = date_pattern.search(context_lines[k])
                                    if date_match:
                                        exam_date = date_match.group(0)
                                        break

                    else:
                        # If exam found but no date yet, search forward a few lines
                        if not exam_date:
                            for k in range(offset, min(len(context_lines), offset+5)):
                                date_match = date_pattern.search(context_lines[k])
                                if date_match:
                                    exam_date = date_match.group(0)
                                    break

                    completed[subject].append((exam_status, exam_score, base_month, exam_date))
                    break  # Stop checking other terms for this subject in this line

    unique_completed = {}
    for subject, entries in completed.items():
        # Prefer entries with date, then higher scores
        sorted_entries = sorted(entries, key=lambda x: (x[3] is not None, x[1] is not None, int(x[1].rstrip('%')) if x[1] else 0, x[2] is not None, x[0] == 'PASS'), reverse=True)
        unique_completed[subject] = sorted_entries[0]

    return unique_completed

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
            output += f"<p><strong>{name}: {details['completion_percentage']:.0f}%</strong></p><ul>"
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
