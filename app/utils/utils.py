from dateutil.parser import parse

def parse_custom_date(date_str):
    return parse(date_str).isoformat() if date_str else None
