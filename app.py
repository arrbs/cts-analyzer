import pdfplumber
import re
import sys
from collections import defaultdict

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

# Define individual subjects with their search terms and the courses (lists) they belong to.
# Each subject can belong to multiple courses.
# You can edit this dictionary to add/remove subjects, terms, or courses.
# Courses are just strings; if you want codes, add them as e.g., "Initial Common Course (ICC)"
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
    # Add more subjects here, e.g.:
    # "Another Subject": {
    #     "search_terms": ["term1", "term2"],
    #     "courses": ["Course1", "Course2"]
    # },
}

# Threshold for "likely" course match (in %)
LIKELY_THRESHOLD = 70

# Dynamically build courses dict from subjects
courses = defaultdict(set)
for subject, data in subjects.items():
    for course in data["courses"]:
        courses[course].add(subject)

def extract_text_from_pdf(pdf_path):
    """Extract all text from the PDF."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def parse_completed_subjects(text):
    """Parse the text to find completed subjects, dates, pass/fail status, score, and base month."""
    completed = defaultdict(list)  # subject -> list of (date, status, score, base_month)

    text_lower = text.lower()
    lines = text.split('\n')

    for i, line in enumerate(lines):
        line_lower = line.lower()
        for subject, data in subjects.items():
            for term in data["search_terms"]:
                term_lower = term.lower()
                if term_lower in line_lower:  # Narrow to line for precision
                    # Get context: 10 lines before, 50 after to capture exam at bottom
                    start = max(0, i - 10)
                    end = min(len(lines), i + 50)
                    context = ' '.join(lines[start:end]).lower()
                    context_lines = lines[start:end]

                    # Find base month
                    base_month_match = re.search(r'base month\s*[:|]\s*(\w+)', context, re.I)
                    base_month = base_month_match.group(1).capitalize() if base_month_match else None

                    # Aggressively find exam in context
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

                    # Fallback date if no exam found
                    fallback_date = None
                    if not exam_date:
                        date_patterns = [
                            r'\d{4}-[a-z]{3}-\d{1,2}',  # 2024-Oct-10
                            r'\d{2}-[a-z]{3}-\d{4}',    # 01-Feb-2024
                            r'\d{4}-\d{2}-\d{2}',       # 2024-05-28
                        ]
                        for pattern in date_patterns:
                            date_match = re.search(pattern, context)
                            if date_match:
                                fallback_date = date_match.group(0)
                                break

                    date = exam_date or fallback_date

                    # Fallback status/score if no exam
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

    # Select best entry per subject
    unique_completed = {}
    for subject, entries in completed.items():
        # Prefer entries with score and exam date
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

def print_table(completed):
    print("Subjects Detected:")
    print("-" * 60)
    print(f"{'Subject':<20} {'Date':<12} {'Status':<8} {'Score':<8} {'Base Mo':<7}")
    print("-" * 60)
    for subject, (date, status, score, base_mo) in sorted(completed.items()):
        date_str = date or 'Unknown'
        base_str = base_mo or 'N/A'
        score_str = score or 'N/A'
        color = get_color(status)
        status_colored = f"{color}{status}{RESET}"
        print(f"{subject[:20]:<20} {date_str[:12]:<12} {status_colored:<8} {score_str:<8} {base_str[:7]:<7}")
    print("-" * 60)

def print_courses(results, completed):
    sorted_results = sorted(results.items(), key=lambda x: x[1]['completion_percentage'], reverse=True)
    print("Likely Lists:")
    for name, details in sorted_results:
        perc = details['completion_percentage']
        color = get_color(perc)
        print(f"- {name[:25]:<25} {color}{perc:.0f}%{RESET}")

    print("\nList Details:")
    for name, details in sorted_results:
        if details['completion_percentage'] > 0:  # Show only partial/complete lists
            print(f"{name}: {details['completion_percentage']:.0f}%")
            all_subs = courses[name]
            for sub in sorted(all_subs):
                if sub in completed:
                    date, status, score, base_mo = completed[sub]
                    color = get_color(status)
                    date_str = date or 'Unknown'
                    base_str = base_mo or 'N/A'
                    score_str = score or 'N/A'
                    print(f"  {color}+ {sub:<20} {date_str:<12} {status} {score_str} {base_str}{RESET}")
                else:
                    print(f"  {RED}- {sub}{RESET}")

def analyze_courses(completed):
    results = {}
    for course_name, req_subjects in courses.items():
        total = len(req_subjects)
        completed_count = sum(1 for sub in req_subjects if sub in completed and completed[sub][1] == 'PASS')
        results[course_name] = {'completion_percentage': (completed_count / total * 100) if total else 0}
    return results

def main(pdf_path):
    text = extract_text_from_pdf(pdf_path)
    if not text:
        print("No text extracted.")
        return

    completed = parse_completed_subjects(text)
    print_table(completed)

    results = analyze_courses(completed)
    print_courses(results, completed)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py path_to_pdf.pdf")
        sys.exit(1)
    pdf_path = sys.argv[1]
    main(pdf_path)
