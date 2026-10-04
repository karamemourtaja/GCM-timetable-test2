from seleniumbase import SB
from bs4 import BeautifulSoup
import json
import datetime
import re
import sys

def run_scraper():
    url = 'https://centralmosque.co.uk/prayer-times/'
    print(f"Fetching {url} using SeleniumBase (Undetected Mode)...")
    
    html_content = ""
    try:
        with SB(uc=True, headless=True) as sb:
            sb.uc_open_with_reconnect(url, 5)
            sb.wait_for_element("table", timeout=15)
            html_content = sb.get_page_source()
    except Exception as e:
        print(f"Failed to fetch website: {e}")
        sys.exit(1)

    soup = BeautifulSoup(html_content, 'html.parser')
    rows = soup.find_all('tr')
    print(f"-> Found {len(rows)} table rows in the HTML.")
    
    # Hardcoded column indices mapped exactly to Glasgow Central Mosque's standard layout
    col_idx = {'fajr': 2, 'sunrise': 4, 'zuhr': 5, 'asr1': 7, 'asr2': 8, 'maghrib': 10, 'isha': 12}
    max_required_col = max(col_idx.values())

    parsed_data = {}
    detected_month = None
    detected_year = datetime.datetime.now().year
    months = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}

    for row in rows:
        cells = [c.text.strip() for c in row.find_all(['td', 'th'])]
        
        # Skip rows that don't have enough columns
        if len(cells) <= max_required_col: 
            continue
        
        if not re.search(r'\d{1,2}:\d{2}', cells[col_idx['fajr']]):
            continue
            
        day_str = cells[0].lower() + " " + cells[1].lower()
        day_match = re.search(r'\b([1-9]|[12]\d|3[01])\b', day_str)
        if not day_match:
            continue
            
        day_num = int(day_match.group(1))
        
        if not detected_month:
            for m_name, m_num in months.items():
                if m_name in day_str:
                    detected_month = m_num
                    break
                    
        year_match = re.search(r'(202\d)', day_str)
        if year_match:
            detected_year = int(year_match.group(1))

        asr2 = cells[col_idx['asr2']] if col_idx['asr2'] < len(cells) and cells[col_idx['asr2']] else cells[col_idx['asr1']]
        
        parsed_data[str(day_num)] = {
            "Fajr": cells[col_idx['fajr']], 
            "Sunrise": cells[col_idx['sunrise']], 
            "Zuhr": cells[col_idx['zuhr']],
            "Asr_I": cells[col_idx['asr1']], 
            "Asr_II": asr2, 
            "Maghrib": cells[col_idx['maghrib']], 
            "Isha": cells[col_idx['isha']]
        }

    if not detected_month:
        detected_month = datetime.datetime.now().month

    if len(parsed_data) >= 28:
        output = {
            "metadata": {
                "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "valid_for_month": detected_month,
                "valid_for_year": detected_year
            },
            "schedule": parsed_data
        }
        
        with open('timetable.json', 'w') as f:
            json.dump(output, f, separators=(',', ':'))
        print(f"Success: Parsed {len(parsed_data)} days for {detected_month}/{detected_year}.")
    else:
        print(f"Error: Could not parse enough days (found {len(parsed_data)}).")
        sys.exit(1)

if __name__ == '__main__':
    run_scraper()