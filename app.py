import streamlit as st
import pdfplumber
import re
from collections import defaultdict
import io

# HTML color spans (adapted for markdown)
GREEN = '<span style="color:green">'
RED = '<span style="color:red">'
YELLOW = '<span style="color:orange">'  # Changed yellow to orange for better visibility
RESET = '</span>'

# Subjects dict (same as before, with your added search terms)
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

# ... (rest of functions: extract_text_from_pdf, parse_completed_subjects, get_color, analyze_courses remain the same as in your last version)

def print_table(completed):
    rows = []
    for subject, (date, status, score, base_mo) in sorted(completed.items()):
        date_str = date or 'Unknown'
        base_str = base_mo or 'N/A'
        score_str = score or 'N/A'
        color = get_color(status)
        status_colored = f"{color}{status}{RESET}"
        rows.append([subject, date_str, status_colored, score_str, base_str])
    return rows  # Return for st.table

def print_courses(results, completed):
    sorted_results = sorted(results.items(), key=lambda x: x[1]['completion_percentage'], reverse=True)
    output = "Likely Lists:\n"
    for name, details in sorted_results:
        perc = details['completion_percentage']
        color = get_color(perc)
        output += f"- {name[:25]:<25} {color}{perc:.0f}%{RESET}\n"

    output += "\nList Details:\n"
    for name, details in sorted_results:
        if details['completion_percentage'] > 0:
            output += f"{name}: {details['completion_percentage']:.0f}%\n"
            all_subs = courses[name]
            for sub in sorted(all_subs):
                if sub in completed:
                    date, status, score, base_mo = completed[sub]
                    color = get_color(status)
                    date_str = date or 'Unknown'
                    base_str = base_mo or 'N/A'
                    score_str = score or 'N/A'
                    output += f"  {color}+ {sub:<20} {date_str:<12} {status} {score_str} {base_str}{RESET}\n"
                else:
                    output += f"  {RED}- {sub}{RESET}\n"
    return output

# Streamlit app
st.title("PDF Exam Analyzer")
st.text("Instructions: Drag PDF into the box below or click 'Browse files'. Do NOT drop on the full page.")
uploaded_file = st.file_uploader("Upload PDF", type="pdf")

if uploaded_file is not None:
    if st.button("Process PDF"):
        text = extract_text_from_pdf(uploaded_file)
        if not text:
            st.error("No text extracted from PDF.")
        else:
            completed = parse_completed_subjects(text)
            st.subheader("Subjects Detected")
            table_rows = [["Subject", "Date", "Status", "Score", "Base Mo"]] + print_table(completed)
            st.table(table_rows)  # Use st.table for clean display
            results = analyze_courses(completed)
            st.subheader("Courses Output")
            st.markdown(print_courses(results, completed), unsafe_allow_html=True)
