import re
import requests
import base64
import urllib.parse
import pdfplumber
import os
from html import unescape
from datetime import datetime

LOGIN_URL = "https://start.count-it.eu/nl/account/login"
DASHBOARD_URL = "https://start.count-it.eu/nl/dashboard/?loadblock=supplierturnoveradmin&uid=2&relative=1"
BASE_URL = "https://start.count-it.eu/nl/financial/allperiodssupplier"
PDF_FILE = "/config/countit_report.pdf"

def b64(s: str) -> str:
    return base64.b64encode(s.encode()).decode()

def build_today_url(dept_id: int) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    start = f"{today} 00:00:00"
    end = f"{today} 23:59:59"
    params = {
        "periodsummary": "pdfall",
        "from": b64(start),
        "till": b64(end),
        "department": b64(str(dept_id)),
    }
    return f"{BASE_URL}?{urllib.parse.urlencode(params, quote_via=urllib.parse.quote)}"

def login_session(username, password) -> requests.Session:
    session = requests.Session()
    session.get(LOGIN_URL)
    form_data = {
        "form_name": "forms_form_100",
        "form_companyid": "0_0",
        "form_submit_button": "",
        "forms_form_100_emailaddress": username,
        "forms_form_100_password": password,
        "forms_form_100_2FACode": "",
        "forms_form_100_2FACodeRemember": "",
        "forms_form_100_2FACodeRememberAlways": "",
    }
    resp = session.post(LOGIN_URL, data=form_data, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Login failed ({resp.status_code})")
    return session

def fetch_sales(username=None, password=None) -> dict:
    session = login_session(username, password)
    dash = session.get(DASHBOARD_URL, timeout=30)
    if dash.status_code != 200:
        raise RuntimeError(f"Dashboard request failed ({dash.status_code})")

    html = unescape(dash.text)
    euro_values = re.findall(r"€\s*([\d\.,]+)", html)
    cijfers = []
    for v in euro_values:
        try:
            cijfers.append(float(v.replace(".", "").replace(",", ".")))
        except ValueError:
            cijfers.append(0.0)

    klanten_match = re.search(r"Klanten:\s*(\d+)", html)
    klanten = int(klanten_match.group(1)) if klanten_match else 0

    while len(cijfers) < 4:
        cijfers.append(0.0)

    dag, maand, week, jaar = cijfers[:4]
    return {"day": dag, "month": maand, "week": week, "year": jaar, "customers": klanten}

def fetch_products(username=None, password=None, departments=None) -> list[str]:
    if not departments:
        print("No departments configured")
        return []

    session = login_session(username, password)
    all_products = []

    for city, dept_id in departments.items():
        prefix = city[:3].upper() + " "
        url = build_today_url(dept_id)
        resp = session.get(url, timeout=60)
        if resp.status_code != 200:
            print(f"Skipping {city} (HTTP {resp.status_code})")
            continue

        with open(PDF_FILE, "wb") as f:
            f.write(resp.content)

        debug_path = f"/config/countit_debug_{city}.pdf"
        with open(debug_path, "wb") as debug_file:
            debug_file.write(resp.content)
        print(f"Saved debug PDF for {city}: {len(resp.content)} bytes → {debug_path}")


        try:
            with pdfplumber.open(PDF_FILE) as pdf:
                for page in pdf.pages:
                    for table in page.extract_tables() or []:
                        if not table:
                            continue
                        header = [h.strip().lower() for h in table[0] if h]
                        if header and "product" in header[0]:
                            for row in table[1:]:
                                if not row or not row[0]:
                                    continue
                                name = re.sub(r"^\s*\d+\s*-\s*(?:[A-Z]\s*-\s*)?", "", row[0]).strip()
                                amount = "1"
                                for cell in row:
                                    if cell and re.match(r"^\d+$", cell.strip()):
                                        amount = cell.strip()
                                        break
                                if name:
                                    all_products.append(f"{prefix}{name} ×{amount}")
        except Exception as e:
            print(f"Error parsing PDF for {city}: {e}")
            continue

    try:
        os.remove(PDF_FILE)
    except Exception:
        pass

    return all_products
