from datetime import datetime

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
