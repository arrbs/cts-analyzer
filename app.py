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

def get_date_color(date_str):
    """
    Calculate date-based color for subject completion dates.
    Color transitions from lime green (fresh) to amber (6 months) to red (near expiry).
    Assumes validity period is approximately 24 months from completion.
    """
    if not date_str or date_str == 'N/A':
        return ''  # No color for invalid dates
    
    parsed_date = parse_date(date_str)
    if not parsed_date:
        return ''  # No color for unparseable dates
    
    now = datetime.now()
    days_since = (now - parsed_date).days
    
    # Define color transition points
    # 0 days = bright lime green
    # 6 months (180 days) = amber
    # 24 months (730 days) = red (approaching validity end)
    
    if days_since < 0:
        # Future date - lime green
        return '<span style="color:#32FF32">'  # Bright lime green
    elif days_since <= 180:  # 0-6 months
        # Transition from lime green to amber
        # Lime green: #32FF32 (RGB: 50, 255, 50)
        # Amber: #FFBF00 (RGB: 255, 191, 0)
        ratio = days_since / 180
        red = int(50 + (255 - 50) * ratio)
        green = int(255 - (255 - 191) * ratio)
        blue = int(50 - 50 * ratio)
        return f'<span style="color:rgb({red},{green},{blue})">'
    elif days_since <= 730:  # 6-24 months
        # Transition from amber to red
        # Amber: #FFBF00 (RGB: 255, 191, 0)
        # Red: #FF0000 (RGB: 255, 0, 0)
        ratio = (days_since - 180) / (730 - 180)
        red = 255  # Stay at 255
        green = int(191 * (1 - ratio))
        blue = 0  # Stay at 0
        return f'<span style="color:rgb({red},{green},{blue})">'
    else:  # Over 24 months
        # Solid red
        return '<span style="color:#FF0000">'

def generate_table(completed, subject_filter=None):
    """Generate HTML table for completed subjects, optionally filtered by subject_filter list"""
    output = "<table><thead><tr><th>Subject</th><th>Status</th><th>Score</th><th>Base Month</th><th>Date</th></tr></thead><tbody>"
    
    # Filter completed subjects if subject_filter is provided
    filtered_completed = completed
    if subject_filter:
        filtered_completed = {k: v for k, v in completed.items() if k in subject_filter}
    
    for subject, (status, score, base_month, date) in sorted(filtered_completed.items()):
        base_str = base_month or 'N/A'
        score_str = score or 'N/A'
        date_str = format_date(date)
        color = get_color(status)
        status_colored = f"{color}{status}{RESET}"
        
        # Apply date-based color to the date column
        date_color = get_date_color(date)
        date_colored = f"{date_color}{date_str}{RESET}" if date_color else date_str
        
        output += f"<tr><td>{subject}</td><td>{status_colored}</td><td>{score_str}</td><td>{base_str}</td><td>{date_colored}</td></tr>"
    output += "</tbody></table>"
    return output

def generate_courses(results, completed, subject_filter=None):
    """Generate HTML for course analysis results, optionally filtered by subject_filter list"""
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
            dates = []
            for sub in courses[name]:
                if sub in completed and completed[sub][0] == 'PASS' and completed[sub][3]:
                    # Apply subject filter if provided
                    if subject_filter is None or sub in subject_filter:
                        parsed_date = parse_date(completed[sub][3])
                        if parsed_date:
                            dates.append(parsed_date)
            if dates:
                start_date = min(dates).strftime('%d %B %Y')
                end_date = max(dates).strftime('%d %B %Y')
                date_info = f" - Start: {start_date}, End: {end_date}"
            output += f"<p><strong>{name}: {perc:.0f}%{date_info}</strong></p>"
            output += "<table><thead><tr><th>Subject</th><th>Status</th><th>Score</th><th>Base Month</th><th>Date</th></tr></thead><tbody>"
            all_subs = courses[name]
            for sub in sorted(all_subs):
                # Apply subject filter if provided
                if subject_filter is None or sub in subject_filter:
                    if sub in completed:
                        status, score, base_mo, date = completed[sub]
                        color = get_color(status)
                        base_str = base_mo or 'N/A'
                        score_str = score or 'N/A'
                        date_str = format_date(date)
                        status_colored = f"{color}{status}{RESET}"
                        
                        # Apply date-based color to the date column
                        date_color = get_date_color(date)
                        date_colored = f"{date_color}{date_str}{RESET}" if date_color else date_str
                        
                        output += f"<tr><td>{sub}</td><td>{status_colored}</td><td>{score_str}</td><td>{base_str}</td><td>{date_colored}</td></tr>"
                    else:
                        output += f"<tr><td>{sub}</td><td>{RED}Not Completed{RESET}</td><td>N/A</td><td>N/A</td><td>N/A</td></tr>"
            output += "</tbody></table>"
    return output

def analyze_courses(completed, subject_filter=None):
    """Analyze course completion, optionally filtered by subject_filter list"""
    results = {}
    for course_name, req_subjects in courses.items():
        # Filter required subjects if subject_filter is provided
        if subject_filter:
            filtered_req_subjects = req_subjects.intersection(set(subject_filter))
        else:
            filtered_req_subjects = req_subjects
            
        total = len(filtered_req_subjects)
        if total == 0:
            continue  # Skip courses with no subjects in the filter
            
        completed_count = sum(1 for sub in filtered_req_subjects if sub in completed and completed[sub][0] == 'PASS')
        results[course_name] = {'completion_percentage': (completed_count / total * 100) if total else 0}
    return results

def analyze_student(completed_subjects, student_name, subject_filter=None):
    """Analyze a single student's completed subjects and return best course match with details."""
    if not completed_subjects:
        return None
    
    # Analyze courses for this student with filtering
    results = analyze_courses(completed_subjects, subject_filter)
    
    if not results:
        return None
    
    # Find the course with highest completion percentage
    sorted_results = sorted(results.items(), key=lambda x: x[1]['completion_percentage'], reverse=True)
    best_course = sorted_results[0]
    best_course_name = best_course[0]
    best_completion_percentage = best_course[1]['completion_percentage']
    
    # Get subjects for the best course
    best_course_subjects = courses[best_course_name]
    
    # Apply subject filter if provided
    if subject_filter:
        best_course_subjects = best_course_subjects.intersection(set(subject_filter))
    
    # Calculate date range and missing subjects for the best course
    completed_dates = []
    missing_subjects = []
    completed_subjects_in_course = []
    
    for subject in best_course_subjects:
        if subject in completed_subjects and completed_subjects[subject][0] == 'PASS':
            date_str = completed_subjects[subject][3]
            if date_str:
                parsed_date = parse_date(date_str)
                if parsed_date:
                    completed_dates.append(parsed_date)
            completed_subjects_in_course.append(subject)
        else:
            missing_subjects.append(subject)
    
    # Determine start and end dates
    start_date = None
    end_date = None
    if completed_dates:
        start_date = min(completed_dates).strftime('%d %B %Y')
        end_date = max(completed_dates).strftime('%d %B %Y')
    
    return {
        'student_name': student_name,
        'best_course': best_course_name,
        'completion_percentage': best_completion_percentage,
        'start_date': start_date,
        'end_date': end_date,
        'missing_subjects': missing_subjects,
        'completed_subjects': completed_subjects,
        'all_courses': sorted_results
    }

def process_bulk_pdfs(uploaded_files, subject_filter=None):
    """Process multiple PDFs, treating each as a different student."""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    student_analyses = []
    
    # Process each PDF as a different student
    for i, uploaded_file in enumerate(uploaded_files):
        status_text.text(f"Processing {uploaded_file.name}...")
        
        text = extract_text_from_pdf(uploaded_file)
        if text:
            # Extract username if available, otherwise use filename
            username = extract_username(text)
            if not username:
                username = uploaded_file.name.replace('.pdf', '').replace('_', ' ')
            
            completed = parse_completed_subjects(text)
            if completed:
                analysis = analyze_student(completed, username, subject_filter)
                if analysis:
                    analysis['filename'] = uploaded_file.name
                    student_analyses.append(analysis)
        
        progress_bar.progress((i + 1) / len(uploaded_files))
    
    status_text.text("Analysis complete!")
    
    if not student_analyses:
        st.error("No subjects detected in any of the uploaded PDFs.")
        return
    
    # Display results for each student
    st.markdown("---")
    st.markdown("## Student Analysis Results")
    st.markdown(f"**Total Students Analyzed:** {len(student_analyses)}")
    
    # Show filter status if applied
    if subject_filter:
        st.markdown(f"**Filtered by subjects:** {', '.join(sorted(subject_filter))}")
    
    for i, analysis in enumerate(student_analyses, 1):
        st.markdown("---")
        
        # Student header
        student_display_name = analysis['student_name']
        if analysis['filename'] != f"{student_display_name}.pdf":
            student_display_name = f"{student_display_name} ({analysis['filename']})"
        
        st.markdown(f"### Student {i}: {student_display_name}")
        
        if subject_filter:
            # When filter is applied, show simple filtered results instead of "most likely" suggestions
            filtered_completed = {k: v for k, v in analysis['completed_subjects'].items() if k in subject_filter}
            
            if filtered_completed:
                st.markdown("**Filtered Subjects:**")
                st.markdown(generate_table(filtered_completed, subject_filter), unsafe_allow_html=True)
                
                # Show completion statistics for filtered subjects
                total_filtered = len(subject_filter)
                completed_filtered = len(filtered_completed)
                completion_rate = (completed_filtered / total_filtered * 100) if total_filtered > 0 else 0
                completion_color = get_color(completion_rate)
                st.markdown(f"**Completion Rate for Selected Subjects:** {completion_color}{completion_rate:.1f}% ({completed_filtered}/{total_filtered}){RESET}", unsafe_allow_html=True)
                
                # Show missing subjects from the filter
                missing_from_filter = [subj for subj in subject_filter if subj not in filtered_completed]
                if missing_from_filter:
                    st.markdown("**Missing from Selected Subjects:**")
                    missing_list = "".join([f"<li>{RED}{subject}{RESET}</li>" for subject in sorted(missing_from_filter)])
                    st.markdown(f"<ul>{missing_list}</ul>", unsafe_allow_html=True)
            else:
                st.markdown(f"**{RED}No selected subjects found for this student{RESET}**", unsafe_allow_html=True)
                
            # Show all detected subjects in expandable section
            if analysis['completed_subjects']:
                with st.expander(f"View All Detected Subjects for {analysis['student_name']}"):
                    st.markdown(generate_table(analysis['completed_subjects']), unsafe_allow_html=True)
        else:
            # Original behavior when no filter is applied - show "most likely" course suggestions
            # Most likely course set
            completion_color = get_color(analysis['completion_percentage'])
            st.markdown(f"**Most Likely Course Set:** {analysis['best_course']}")
            st.markdown(f"**Completion Rate:** {completion_color}{analysis['completion_percentage']:.1f}%{RESET}", unsafe_allow_html=True)
            
            # Start and finish dates
            if analysis['start_date'] and analysis['end_date']:
                if analysis['start_date'] == analysis['end_date']:
                    st.markdown(f"**Completion Date:** {analysis['start_date']}")
                else:
                    st.markdown(f"**Start Date:** {analysis['start_date']}")
                    st.markdown(f"**Finish Date:** {analysis['end_date']}")
            else:
                st.markdown("**Dates:** Not available")
            
            # Missing subjects
            if analysis['missing_subjects']:
                st.markdown("**Missing Subjects:**")
                missing_list = "".join([f"<li>{RED}{subject}{RESET}</li>" for subject in sorted(analysis['missing_subjects'])])
                st.markdown(f"<ul>{missing_list}</ul>", unsafe_allow_html=True)
            else:
                st.markdown(f"**{GREEN}All subjects completed for this course set!{RESET}**", unsafe_allow_html=True)
            
            # Show completed subjects in expandable section
            with st.expander(f"View {analysis['student_name']}'s Completed Subjects"):
                st.markdown(generate_table(analysis['completed_subjects'], subject_filter), unsafe_allow_html=True)
            
            # Show all course completion rates in expandable section
            with st.expander(f"View All Course Completion Rates for {analysis['student_name']}"):
                for course_name, details in analysis['all_courses']:
                    perc = details['completion_percentage']
                    color = get_color(perc)
                    st.markdown(f"- **{course_name}:** {color}{perc:.1f}%{RESET}", unsafe_allow_html=True)
    
    # Summary statistics
    st.markdown("---")
    st.markdown("### Overall Summary")
    
    if subject_filter:
        # For filtered mode, show statistics about the selected subjects
        total_students = len(student_analyses)
        completion_rates = []
        
        for analysis in student_analyses:
            filtered_completed = {k: v for k, v in analysis['completed_subjects'].items() if k in subject_filter}
            total_filtered = len(subject_filter)
            completed_filtered = len(filtered_completed)
            completion_rate = (completed_filtered / total_filtered * 100) if total_filtered > 0 else 0
            completion_rates.append(completion_rate)
        
        # Calculate how many students have completed each filtered subject
        subject_completion_counts = {}
        for subject in subject_filter:
            count = sum(1 for analysis in student_analyses if subject in analysis['completed_subjects'])
            subject_completion_counts[subject] = count
        
        st.markdown(f"**Selected Subjects Completion Summary:**")
        for subject, count in sorted(subject_completion_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_students * 100) if total_students > 0 else 0
            color = get_color(percentage)
            st.markdown(f"- **{subject}:** {color}{count}/{total_students} students ({percentage:.1f}%){RESET}", unsafe_allow_html=True)
        
        # Average completion rate for selected subjects
        avg_completion = sum(completion_rates) / len(completion_rates) if completion_rates else 0
        avg_color = get_color(avg_completion)
        st.markdown(f"**Average Completion Rate for Selected Subjects:** {avg_color}{avg_completion:.1f}%{RESET}", unsafe_allow_html=True)
    else:
        # Original behavior when no filter is applied
        # Count how many students are in each course type
        course_counts = {}
        for analysis in student_analyses:
            course = analysis['best_course']
            if course not in course_counts:
                course_counts[course] = 0
            course_counts[course] += 1
        
        st.markdown("**Students by Most Likely Course Set:**")
        for course, count in sorted(course_counts.items(), key=lambda x: x[1], reverse=True):
            st.markdown(f"- **{course}:** {count} student{'s' if count != 1 else ''}")
        
        # Average completion rate
        avg_completion = sum(a['completion_percentage'] for a in student_analyses) / len(student_analyses)
        avg_color = get_color(avg_completion)
        st.markdown(f"**Average Completion Rate:** {avg_color}{avg_completion:.1f}%{RESET}", unsafe_allow_html=True)

# Streamlit app
st.title("PDF Exam Analyzer")

# Mode selection
mode = st.radio("Select Mode:", ["Single Student", "Multiple Students"], horizontal=True)

# Subject filter - available in both modes
st.markdown("---")
st.markdown("**Optional Subject Filter**: Select specific subjects you're interested in (e.g., CRM, SMS). Leave empty to analyze all subjects.")

# Get all subject names and sort them
all_subjects = sorted(subjects.keys())
selected_subjects = st.multiselect(
    "Select subjects of interest (optional):",
    all_subjects,
    help="Choose subjects you want to focus on. If none selected, all detected subjects will be analyzed."
)

# Convert to None if empty for easier handling
subject_filter = selected_subjects if selected_subjects else None

st.markdown("---")

if mode == "Single Student":
    st.markdown("**Instructions:** Drag and drop your PDF into the box below (or click 'Browse files' to select). Then click 'Process PDF'. Do NOT drop the PDF on the full page—it will open the file instead.")
    uploaded_file = st.file_uploader("Upload PDF", type="pdf")

    if uploaded_file is not None:
        if st.button("Process PDF"):
            text = extract_text_from_pdf(uploaded_file)
            if not text:
                st.error("No text extracted from PDF. The file may be scanned/image-only or corrupted.")
            else:
                username = extract_username(text)
                completed = parse_completed_subjects(text)
                if completed:
                    if username:
                        st.markdown(f"<h1>Report for {username}</h1>", unsafe_allow_html=True)
                    
                    # Show filter status if applied
                    if subject_filter:
                        st.markdown(f"**Analyzing subjects:** {', '.join(sorted(subject_filter))}")
                        # Check if any filtered subjects were found
                        filtered_completed = {k: v for k, v in completed.items() if k in subject_filter}
                        if not filtered_completed:
                            st.warning(f"None of the selected subjects ({', '.join(sorted(subject_filter))}) were found in this PDF.")
                            st.markdown("**All detected subjects:**")
                            st.markdown(", ".join(sorted(completed.keys())))
                        else:
                            # Show results only if filtered subjects were found
                            st.subheader("Subjects Detected")
                            st.markdown(generate_table(completed, subject_filter), unsafe_allow_html=True)
                            results = analyze_courses(completed, subject_filter)
                            if results:  # Only show if there are results
                                st.markdown(generate_courses(results, completed, subject_filter), unsafe_allow_html=True)
                    else:
                        # No filter applied, show all results
                        st.subheader("Subjects Detected")
                        st.markdown(generate_table(completed, subject_filter), unsafe_allow_html=True)
                        results = analyze_courses(completed, subject_filter)
                        if results:  # Only show if there are results
                            st.markdown(generate_courses(results, completed, subject_filter), unsafe_allow_html=True)
                else:
                    st.warning("No subjects detected in the PDF.")

else:  # Multiple Students
    st.markdown("**Instructions:** Upload multiple PDF files below. Each PDF will be treated as a different student. For each student, the system will analyze and provide:")
    st.markdown("- The most likely set of subjects (Initial, Module 1, Module 2)")
    st.markdown("- When it was done (start and finish dates)")
    st.markdown("- Which subjects are missing")
    uploaded_files = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)
    
    if uploaded_files:
        st.write(f"Uploaded {len(uploaded_files)} PDF(s)")
        if st.button("Process All PDFs"):
            process_bulk_pdfs(uploaded_files, subject_filter)
