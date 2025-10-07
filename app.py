import streamlit as st
import pdfplumber
import re
from collections import defaultdict
from datetime import datetime, timedelta

# HTML color spans
GREEN = '<span style="color:green">'
RED = '<span style="color:red">'
YELLOW = '<span style="color:orange">'  # Orange for better visibility than yellow
RESET = '</span>'

# Subjects dict (with all your added search terms)
subjects = {
    "ADS-B": {
        "search_terms": ["ADS-B Overview", "ADS-B Exam"],
        "courses": ["Initial (P121)", "Initial (P135)", "Odd Year (P135)", "Module 1 (P121)"],
        "validity_months": 24
    },
    "Weather": {
        "search_terms": ["Aviation Weather Theory", "Aviation Weather Theory Exam"],
        "courses": ["Initial (P121)", "Initial (P135)", "Odd Year (P135)", "Module 1 (P121)"],
        "validity_months": 24
    },
    "Aerodynamics": {
        "search_terms": ["Helicopter Aerodynamics", "Helicopter Specific Exam"],
        "courses": ["Initial (P121)", "Initial (P135)", "Odd Year (P135)", "Module 1 (P121)"],
        "validity_months": 24
    },
    "Airspace": {
        "search_terms": ["Airspace Overview", "Airspace Overview Exam"],
        "courses": ["Initial (P121)", "Initial (P135)", "Odd Year (P135)", "Module 1 (P121)"],
        "validity_months": 24
    },
    "Brownout": {
        "search_terms": ["Flat-light, Whiteout, and Brownout Conditions"],
        "courses": ["Initial (P121)", "Initial (P135)", "Odd Year (P135)", "Module 1 (P121)"],
        "validity_months": 24
    },
    "CFIT": {
        "search_terms": ["Controlled Flight into Terrain Avoidance (CFIT, TAWS, and ALAR) - RW", "Controlled Flight into Terrain Avoidance RW Exam"],
        "courses": ["Initial (P121)", "Initial (P135)", "Odd Year (P135)", "Even Year (P135)", "Module 1 (P121)"],
        "validity_months": 24
    },
    "Fire Classes": {
        "search_terms": ["Classes of Fire and Portable Fire Extinguishers", "Portable Fire Extinguisher Exam"],
        "courses": ["Initial (P121)", "Module 1 (P121)"],
        "validity_months": 24
    },
    "GPS": {
        "search_terms": ["GPS (RW IFR-VFR)", "GPS (RW IFR) Exam"],
        "courses": ["Initial (P121)", "Initial (P135)", "Odd Year (P135)", "Module 1 (P121)"],
        "validity_months": 24
    },
    "External Lighting": {
        "search_terms": ["Helicopter External Lighting", "Helicopter External Lighting Exam"],
        "courses": ["Initial (P121)", "Initial (P135)", "Odd Year (P135)", "Module 2 (121)"],
        "validity_months": 24
    },
    "METAR and TAF": {
        "search_terms": ["METAR and TAF", "METAR and TAF Exam"],
        "courses": ["Initial (P121)", "Initial (P135)", "Even Year (P135)", "Module 2 (121)"],
        "validity_months": 24
    },
    "First Aid": {
        "search_terms": ["Physiology and First Aid (RW)", "Physiology and First Aid (RW) Exam"],
        "courses": ["Initial (P121)", "Initial (P135)", "Odd Year (P135)", "Even Year (P135)", "Module 1 (P121)", "Module 2 (121)"],
        "validity_months": 12
    },
    "Runway Incursion": {
        "search_terms": ["Runway Incursion", "Runway Incursion Exam"],
        "courses": ["Initial (P121)", "Initial (P135)", "Even Year (P135)", "Module 2 (121)"],
        "validity_months": 24
    },
    "Survival": {
        "search_terms": ["Survival", "Survival Exam"],
        "courses": ["Initial (P121)", "Initial (P135)", "Even Year (P135)", "Module 2 (121)"],
        "validity_months": 24
    },
    "Traffic Advisory System": {
        "search_terms": ["Traffic Advisory System (TAS)", "Traffic Advisory System"],
        "courses": ["Initial (P121)", "Initial (P135)", "Even Year (P135)", "Module 2 (121)"],
        "validity_months": 24
    },
    "Traffic Collision Avoidance System": {
        "search_terms": ["TCAS II ", "Traffic Collision Avoidance System (TCASII)", "TCAS II - Exam"],
        "courses": ["Initial (P121)", "Initial (P135)", "Even Year (P135)", "Module 2 (121)"],
        "validity_months": 24
    },
    "Windshear": {
        "search_terms": ["Windshear (RW)", "Helicopter Windshear Exam"],
        "courses": ["Initial (P121)", "Initial (P135)", "Even Year (P135)", "Module 2 (121)"],
        "validity_months": 24
    },
    "CRM": {
        "search_terms": ["CRM-ADM - Rotor Wing", "Crew Resource Management - Rotor Wing Exam"],
        "courses": ["Initial (P121)", "Initial (P135)", "Odd Year (P135)", "Even Year (P135)", "Module 1 (P121)", "Module 2 (121)"],
        "validity_months": 12
    },
    "Basic Indoc": {
        "search_terms": ["The Helicopter and Jet Company - Indoc (NEW)", "The Helicopter Company - Indoc - SUPERCEDED", "THC - Indoc - EXAM"],
        "courses": ["Initial (P121)", "Initial (P135)"],
        "validity_months": None  # Infinite validity
    },
    "SMS": {
        "search_terms": ["The Helicopter and Jet Company - SMS", "THC - SMS Exam", "SMS Exam"],
        "courses": ["Initial (P121)", "Initial (P135)", "DG + SMS"],
        "validity_months": 24
    },
    "Hazmat": {
        "search_terms": ["Hazmat - Will Not Carry", "Hazmat Will Not Carry Exam"],
        "courses": ["Initial (P121)", "Initial (P135)", "DG + SMS"],
        "validity_months": 24
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

date_pattern = re.compile(r'(\d{1,2}\s*-\s*[a-z]{3}\s*-\s*\d{4})|(\d{4}\s*-\s*[a-z]{3}\s*-\s*\d{1,2})|(\d{1,2}/\d{1,2}/\d{4})', re.I)

def parse_date(date_str):
    if not date_str:
        return None
    date_str = date_str.replace(' ', '')  # Remove spaces
    formats = ['%d-%b-%Y', '%Y-%b-%d', '%m/%d/%Y']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            pass
    return None

def format_date(date_str):
    parsed = parse_date(date_str)
    if parsed:
        return parsed.strftime('%d %B %Y')
    return date_str or 'N/A'

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
                        score_match = re.search(r'(\d+)\s*%\s*(pass|fail|complete)?', sub_line_clean)
                        if score_match:
                            score_num = score_match.group(1)
                            exam_score = score_num + '%'
                            status_str = score_match.group(2) or ''
                            exam_status = 'PASS' if 'pass' in status_str.lower() or 'complete' in status_str.lower() or int(score_num) >= 70 else 'FAIL'
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

def extract_username(text):
    # Search near the top: first 10 lines or so
    lines = text.split('\n')[:10]
    username_pattern = re.compile(r'(\w+@thc)', re.I)
    for line in lines:
        match = username_pattern.search(line)
        if match:
            return match.group(1).split('@')[0]
    return None

def get_color(status_or_perc):
    if isinstance(status_or_perc, str):
        return GREEN if 'PASS' in status_or_perc else RED
    else:
        if status_or_perc == 100:
            return GREEN
        else:
            return YELLOW

def get_expiry_status(subject_name, completion_date_str):
    """
    Calculate expiry status for a subject.
    Returns: (status, expiry_date, days_remaining, badge_html)
    status: 'fresh', 'expiring_soon', 'expired', 'infinite'
    """
    if not completion_date_str:
        return ('unknown', None, None, '')
    
    validity_months = subjects.get(subject_name, {}).get('validity_months')
    
    # Infinite validity (Basic Indoc)
    if validity_months is None:
        return ('infinite', None, None, '<span style="background: #e3f2fd; color: #1976d2; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; margin-left: 0.5rem;">∞ Valid</span>')
    
    completion_date = parse_date(completion_date_str)
    if not completion_date:
        return ('unknown', None, None, '')
    
    expiry_date = completion_date + timedelta(days=validity_months * 30)
    today = datetime.now()
    days_remaining = (expiry_date - today).days
    
    if days_remaining < 0:
        # Expired
        return ('expired', expiry_date, days_remaining, 
                f'<span style="background: #ffebee; color: #c62828; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; margin-left: 0.5rem;">⚠️ Expired</span>')
    elif days_remaining <= 60:
        # Expiring soon (within 60 days)
        return ('expiring_soon', expiry_date, days_remaining,
                f'<span style="background: #fff3e0; color: #e65100; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; margin-left: 0.5rem;">⏰ {days_remaining}d left</span>')
    else:
        # Fresh
        return ('fresh', expiry_date, days_remaining,
                f'<span style="background: #e8f5e9; color: #2e7d32; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; margin-left: 0.5rem;">✓ Valid</span>')

def generate_table(completed):
    output = "<table><thead><tr><th>Subject</th><th>Status</th><th>Score</th><th>Base Month</th><th>Date</th><th>Expiry Status</th></tr></thead><tbody>"
    for subject, (status, score, base_month, date) in sorted(completed.items()):
        base_str = base_month or 'N/A'
        score_str = score or 'N/A'
        date_str = format_date(date)
        color = get_color(status)
        status_colored = f"{color}{status}{RESET}"
        
        # Get expiry status
        expiry_status, expiry_date, days_remaining, badge_html = get_expiry_status(subject, date)
        
        output += f"<tr><td>{subject}</td><td>{status_colored}</td><td>{score_str}</td><td>{base_str}</td><td>{date_str}</td><td>{badge_html}</td></tr>"
    output += "</tbody></table>"
    return output

def get_date_range(completed):
    """Get the date range of all completed subjects"""
    dates = []
    for sub in completed:
        if completed[sub][0] == 'PASS' and completed[sub][3]:
            parsed_date = parse_date(completed[sub][3])
            if parsed_date:
                dates.append(parsed_date)
    if dates:
        start_date = min(dates).strftime('%d %B %Y')
        end_date = max(dates).strftime('%d %B %Y')
        return start_date, end_date
    return None, None

def generate_courses(results, completed):
    # Group courses
    course_groups = {
        'P121 Courses': ['Initial (P121)', 'Module 1 (P121)', 'Module 2 (121)'],
        'P135 Courses': ['Initial (P135)', 'Odd Year (P135)', 'Even Year (P135)'],
        'Other': ['DG + SMS']
    }
    
    # Get overall date range
    start_date, end_date = get_date_range(completed)
    
    output = ""
    
    # Show date range prominently at the top
    if start_date and end_date:
        output += f"""
        <div class="date-banner">
            <h2 style='margin: 0; color: white;'>📅 Training Period</h2>
            <p style='margin: 0.5rem 0 0 0; font-size: 1.2rem; font-weight: 500;'>{start_date} — {end_date}</p>
        </div>
        """
    
    output += "<div class='course-summary'>"
    output += "<h3 style='margin-top: 0;'>🎯 Most Likely Course Lists</h3>"
    
    # For each group, find the most likely course
    for group_name, course_list in course_groups.items():
        output += f"<h4>{group_name}:</h4><ul>"
        # Use adjusted percentage for sorting (internal), but display actual counts
        group_results = []
        for name in course_list:
            if name in results:
                adjusted_perc = results[name]['completion_percentage']
                completed_count = results[name]['completed_count']
                total_count = results[name]['total_count']
                group_results.append((name, adjusted_perc, completed_count, total_count))
        
        group_results.sort(key=lambda x: x[1], reverse=True)  # Sort by adjusted percentage
        
        for i, (name, adjusted_perc, completed_count, total_count) in enumerate(group_results):
            # Calculate raw percentage for coloring
            raw_perc = (completed_count / total_count * 100) if total_count > 0 else 0
            color = get_color(raw_perc)
            count_str = f"({completed_count}/{total_count})"
            
            # Create anchor ID for linking
            anchor_id = name.replace(' ', '_').replace('(', '').replace(')', '')
            
            # Check for incomplete/failed subjects
            missing_count = total_count - completed_count
            warning_badge = ""
            if i == 0 and completed_count > 0:  # Most likely course
                if missing_count > 0:
                    # Has missing or failed subjects
                    warning_badge = f' <span style="background: #ffebee; color: #c62828; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.85rem; font-weight: 600; margin-left: 0.5rem;">⚠️ {missing_count} Missing</span>'
            
            # Highlight the most likely (first one after sorting)
            if i == 0 and completed_count > 0:
                if missing_count > 0:
                    # Incomplete - show with warning
                    output += f"<li style='margin: 0.5rem 0; padding: 0.75rem; background: #fff3e0; border-left: 4px solid #f57c00; border-radius: 4px;'><strong>⭐ <a href='#{anchor_id}'>{name}</a> <span style='color: #6c757d;'>{count_str}</span></strong> <span style='background: #fff; color: #f57c00; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.85rem; border: 1px solid #f57c00;'>Most Likely</span>{warning_badge}</li>"
                else:
                    # Complete - show with success
                    output += f"<li style='margin: 0.5rem 0; padding: 0.75rem; background: #e8f5e9; border-left: 4px solid #4caf50; border-radius: 4px;'><strong>⭐ <a href='#{anchor_id}'>{name}</a> <span style='color: #6c757d;'>{count_str}</span></strong> <span style='background: #d4edda; color: #155724; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.85rem;'>✓ Complete & Most Likely</span></li>"
            else:
                output += f"<li style='margin: 0.5rem 0;'><a href='#{anchor_id}'>{name}</a> <span style='color: #6c757d;'>{count_str}</span></li>"
        output += "</ul>"
    
    output += "</div>"
    
    output += "<br><h3 style='color: #2d3748;'>📋 Detailed Course Breakdowns</h3>"
    
    # Show details for each group
    for group_name, course_list in course_groups.items():
        output += f"<h4>{group_name}:</h4>"
        group_results = []
        for name in course_list:
            if name in results:
                adjusted_perc = results[name]['completion_percentage']
                completed_count = results[name]['completed_count']
                total_count = results[name]['total_count']
                group_results.append((name, adjusted_perc, completed_count, total_count))
        
        group_results.sort(key=lambda x: x[1], reverse=True)
        
        for name, adjusted_perc, completed_count, total_count in group_results:
            if completed_count > 0:
                # Create anchor for linking
                anchor_id = name.replace(' ', '_').replace('(', '').replace(')', '')
                
                date_info = ""
                dates = []
                for sub in courses[name]:
                    if sub in completed and completed[sub][0] == 'PASS' and completed[sub][3]:
                        parsed_date = parse_date(completed[sub][3])
                        if parsed_date:
                            dates.append(parsed_date)
                if dates:
                    start_date = min(dates).strftime('%d %B %Y')
                    end_date = max(dates).strftime('%d %B %Y')
                    date_info = f"<br><span style='color: #6c757d; font-size: 0.9rem;'>📅 {start_date} — {end_date}</span>"
                
                output += f"""
                <div class='report-card' id='{anchor_id}' style='margin-top: 1.5rem;'>
                    <h4 style='margin: 0 0 0.5rem 0; color: #2d3748;'>{name} <span style='color: #6c757d; font-weight: normal;'>({completed_count}/{total_count})</span></h4>
                    {date_info}
                </div>
                """
                output += "<table><thead><tr><th>Subject</th><th>Status</th><th>Score</th><th>Base Month</th><th>Date</th><th>Expiry Status</th></tr></thead><tbody>"
                all_subs = courses[name]
                for sub in sorted(all_subs):
                    if sub in completed:
                        status, score, base_mo, date = completed[sub]
                        color = get_color(status)
                        base_str = base_mo or 'N/A'
                        score_str = score or 'N/A'
                        date_str = format_date(date)
                        status_colored = f"{color}{status}{RESET}"
                        
                        # Get expiry status
                        expiry_status, expiry_date, days_remaining, badge_html = get_expiry_status(sub, date)
                        
                        output += f"<tr><td>{sub}</td><td>{status_colored}</td><td>{score_str}</td><td>{base_str}</td><td>{date_str}</td><td>{badge_html}</td></tr>"
                    else:
                        output += f"<tr><td>{sub}</td><td>{RED}Not Completed{RESET}</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td></tr>"
                output += "</tbody></table>"
    
    # Add all subjects at the bottom
    output += "<br><br><h3 style='color: #2d3748;'>📚 All Subjects Overview</h3>"
    output += "<div class='report-card'>"
    output += generate_table(completed)
    output += "</div>"
    
    return output
    output = "<h3>Likely Lists (Most Likely in Each Group):</h3>"
    
    # For each group, find the most likely course
    for group_name, course_list in course_groups.items():
        output += f"<h4>{group_name}:</h4><ul>"
        # Use adjusted percentage for sorting (internal), but display actual counts
        group_results = []
        for name in course_list:
            if name in results:
                adjusted_perc = results[name]['completion_percentage']
                completed_count = results[name]['completed_count']
                total_count = results[name]['total_count']
                group_results.append((name, adjusted_perc, completed_count, total_count))
        
        group_results.sort(key=lambda x: x[1], reverse=True)  # Sort by adjusted percentage
        
        for i, (name, adjusted_perc, completed_count, total_count) in enumerate(group_results):
            # Calculate raw percentage for coloring
            raw_perc = (completed_count / total_count * 100) if total_count > 0 else 0
            color = get_color(raw_perc)
            count_str = f"({completed_count}/{total_count})"
            
            # Highlight the most likely (first one after sorting)
            if i == 0 and completed_count > 0:
                output += f"<li><strong>⭐ {name} {count_str}: {color}{completed_count}/{total_count}{RESET}</strong> (Most Likely)</li>"
            else:
                output += f"<li>{name} {count_str}: {color}{completed_count}/{total_count}{RESET}</li>"
        output += "</ul>"
    
    output += "<h3>List Details:</h3>"
    
    # Show details for each group
    for group_name, course_list in course_groups.items():
        output += f"<h4>{group_name}:</h4>"
        group_results = []
        for name in course_list:
            if name in results:
                adjusted_perc = results[name]['completion_percentage']
                completed_count = results[name]['completed_count']
                total_count = results[name]['total_count']
                group_results.append((name, adjusted_perc, completed_count, total_count))
        
        group_results.sort(key=lambda x: x[1], reverse=True)
        
        for name, adjusted_perc, completed_count, total_count in group_results:
            if completed_count > 0:
                date_info = ""
                dates = []
                for sub in courses[name]:
                    if sub in completed and completed[sub][0] == 'PASS' and completed[sub][3]:
                        parsed_date = parse_date(completed[sub][3])
                        if parsed_date:
                            dates.append(parsed_date)
                if dates:
                    start_date = min(dates).strftime('%d %B %Y')
                    end_date = max(dates).strftime('%d %B %Y')
                    date_info = f" - Start: {start_date}, End: {end_date}"
                output += f"<p><strong>{name} ({completed_count}/{total_count}){date_info}</strong></p>"
                output += "<table><thead><tr><th>Subject</th><th>Status</th><th>Score</th><th>Base Month</th><th>Date</th></tr></thead><tbody>"
                all_subs = courses[name]
                for sub in sorted(all_subs):
                    if sub in completed:
                        status, score, base_mo, date = completed[sub]
                        color = get_color(status)
                        base_str = base_mo or 'N/A'
                        score_str = score or 'N/A'
                        date_str = format_date(date)
                        status_colored = f"{color}{status}{RESET}"
                        output += f"<tr><td>{sub}</td><td>{status_colored}</td><td>{score_str}</td><td>{base_str}</td><td>{date_str}</td></tr>"
                    else:
                        output += f"<tr><td>{sub}</td><td>{RED}Not Completed{RESET}</td><td>N/A</td><td>N/A</td><td>N/A</td></tr>"
                output += "</tbody></table>"
    return output

def analyze_courses(completed):
    results = {}
    total_passed = len([s for s in completed if completed[s][0] == 'PASS'])
    
    for course_name, req_subjects in courses.items():
        total = len(req_subjects)
        completed_count = sum(1 for sub in req_subjects if sub in completed and completed[sub][0] == 'PASS')
        completion_perc = (completed_count / total * 100) if total else 0
        
        # Smart classification: if a student passed MORE subjects than exist in this course,
        # and got 100% of this course, they likely took a larger course
        # Penalize smaller courses when student has passed many more subjects
        penalty = 0
        if completion_perc == 100 and total_passed > total:
            # The more extra subjects they passed, the less likely this smaller course is
            extra_subjects = total_passed - total
            penalty = min(extra_subjects * 5, 40)  # Max 40% penalty
        
        adjusted_perc = max(0, completion_perc - penalty)
        results[course_name] = {
            'completion_percentage': adjusted_perc,
            'completed_count': completed_count,
            'total_count': total
        }
    
    return results

# Custom CSS for beautiful design
st.markdown("""
<style>
    /* Main container styling */
    .main {
        background-color: #f8f9fa;
    }
    
    /* Card-style containers */
    .report-card {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
    
    /* Date range banner */
    .date-banner {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    /* Course summary cards */
    .course-summary {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
    }
    
    /* Table styling */
    table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin: 1rem 0;
        background: white;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }
    
    thead th {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        text-align: left;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.85rem;
        letter-spacing: 0.5px;
    }
    
    tbody tr {
        border-bottom: 1px solid #e9ecef;
        transition: background-color 0.2s;
    }
    
    tbody tr:hover {
        background-color: #f8f9fa;
    }
    
    tbody td {
        padding: 1rem;
        color: #495057;
    }
    
    /* Section headers */
    h2, h3, h4 {
        color: #2d3748;
        font-weight: 600;
        margin-top: 2rem;
    }
    
    /* Links */
    a {
        color: #667eea;
        text-decoration: none;
        font-weight: 500;
        transition: color 0.2s;
    }
    
    a:hover {
        color: #764ba2;
        text-decoration: underline;
    }
    
    /* Star icon */
    strong {
        color: #2d3748;
    }
    
    /* Navigation buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Dividers */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #e9ecef, transparent);
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Streamlit app
st.title("📊 PDF Exam Analyzer")

# Only show upload section if results haven't been processed
if 'pdf_results' not in st.session_state or not st.session_state.pdf_results:
    st.markdown("""
    <div class="report-card">
        <h3>📤 Upload Training Records</h3>
        <p>Upload one or more PDF training transcripts to analyze completion status and identify likely course lists.</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader("Upload PDF(s)", type="pdf", accept_multiple_files=True, label_visibility="collapsed")
    
    if uploaded_files:
        if st.button("🚀 Process PDFs", type="primary", use_container_width=True):
            # Process all PDFs and store results in session state
            st.session_state.pdf_results = []
            
            with st.spinner('Processing PDFs...'):
                for uploaded_file in uploaded_files:
                    text = extract_text_from_pdf(uploaded_file)
                    if text:
                        username = extract_username(text)
                        completed = parse_completed_subjects(text)
                        if completed:
                            results = analyze_courses(completed)
                            st.session_state.pdf_results.append({
                                'filename': uploaded_file.name,
                                'username': username,
                                'completed': completed,
                                'results': results
                            })
            
            # Initialize navigation index
            if st.session_state.pdf_results:
                st.session_state.current_index = 0
                st.rerun()
            else:
                st.warning("No subjects detected in any of the uploaded PDFs.")

# Display results with navigation
if 'pdf_results' in st.session_state and st.session_state.pdf_results:
    total_pdfs = len(st.session_state.pdf_results)
    current_idx = st.session_state.get('current_index', 0)
    
    # Reset button in top right
    col_reset1, col_reset2 = st.columns([5, 1])
    with col_reset2:
        if st.button("🔄 New Analysis", type="secondary"):
            st.session_state.pdf_results = []
            st.session_state.current_index = 0
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Navigation controls
    nav_col1, nav_col2, nav_col3 = st.columns([1, 3, 1])
    
    with nav_col1:
        if st.button("← Previous", disabled=(current_idx == 0), use_container_width=True):
            st.session_state.current_index = max(0, current_idx - 1)
            st.rerun()
    
    with nav_col2:
        st.markdown(f"""
        <div style='text-align: center; padding: 0.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
        color: white; border-radius: 8px; font-weight: 600; margin-bottom: 1rem;'>
        PDF {current_idx + 1} of {total_pdfs}
        </div>
        """, unsafe_allow_html=True)
    
    with nav_col3:
        if st.button("Next →", disabled=(current_idx >= total_pdfs - 1), use_container_width=True):
            st.session_state.current_index = min(total_pdfs - 1, current_idx + 1)
            st.rerun()
    
    # Display current PDF results
    current_result = st.session_state.pdf_results[current_idx]
    
    # File name - small and subtle
    st.markdown(f"""
    <p style='color: #6c757d; font-size: 0.85rem; margin: 0.5rem 0 1rem 0;'>
        📄 {current_result['filename']}
    </p>
    """, unsafe_allow_html=True)
    
    if current_result['username']:
        st.markdown(f"""
        <div class="report-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white;">
            <h1 style='margin: 0; color: white;'>👤 {current_result['username']}</h1>
        </div>
        """, unsafe_allow_html=True)
    
    # Generate and display the full report (includes date range, likely lists, details, and all subjects at bottom)
    st.markdown(generate_courses(current_result['results'], current_result['completed']), unsafe_allow_html=True)
    
    # Progress indicator at bottom
    st.markdown("<br><br>", unsafe_allow_html=True)
    progress_val = (current_idx + 1) / total_pdfs
    st.progress(progress_val)
    st.markdown(f"""
    <p style='text-align: center; color: #6c757d; font-size: 0.9rem; margin-top: 0.5rem;'>
    Viewing {current_idx + 1} of {total_pdfs} training records
    </p>
    """, unsafe_allow_html=True)
