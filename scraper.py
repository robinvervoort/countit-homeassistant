import re
import requests
import base64
import urllib.parse
import pdfplumber
import os
from html import unescape
from datetime import datetime

# --- URLs ---
LOGIN_URL = "https://start.count-it.eu/nl/account/login"
DASHBOARD_URL = "https://start.count-it.eu/nl/dashboard/?loadblock=supplierturnoveradmin&uid=2&relative=1"
BASE_URL = "https://start.count-it.eu/nl/financial/allperiodssupplier"

# --- Temp file path ---
PDF_FILE = "/config/countit_report.pdf"

# --- Department list (city, id) ---
DEPARTMENTS = [
    ("Hasselt",   135),
    ("Antwerpen", 111),
    ("Kapellen",  112),
    ("Lier",      119),
    ("Mol",       149),
    ("Turnhout",  136),
]


# ---------- Utility helpers ----------
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
    """Perform login and return authenticated session."""
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


# ---------- Dashboard scraping ----------
def fetch_sales(username=None, password=None) -> dict:
    """Scrape the dashboard for daily/monthly/yearly sales and customer count."""
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

    return {
        "day": float(dag),
        "month": float(maand),
        "week": float(week),
        "year": float(jaar),
        "customers": int(klanten),
    }


# ---------- PDF scraping ----------
def fetch_products(username=None, password=None) -> list[str]:
    """Download PDFs for each department and extract product names + sold count."""
    session = login_session(username, password)
    all_products = []

    for city, dept_id in DEPARTMENTS:
        prefix = city[:3].upper() + " "
        url = build_today_url(dept_id)
        resp = session.get(url, timeout=60)
        if resp.status_code != 200:
            # Skip if department request failed
            continue

        with open(PDF_FILE, "wb") as f:
            f.write(resp.content)

        try:
            with pdfplumber.open(PDF_FILE) as pdf:
                for page in pdf.pages:
                    for table in page.extract_tables():
                        if not table:
                            continue

                        header = [h.strip().lower() for h in table[0] if h]
                        if header and "product" in header[0]:
                            for row in table[1:]:
                                if not row or not row[0]:
                                    continue

                                name = re.sub(r"^\s*\d+\s*-\s*(?:[A-Z]\s*-\s*)?", "", row[0]).strip()

                                # find amount sold (# column)
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

    # Clean up temporary file
    try:
        os.remove(PDF_FILE)
    except Exception:
        pass

    return all_products
