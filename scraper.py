import os
import re
import csv
import io
import concurrent.futures
import requests
from flask import Flask, render_template_string, request, Response

app = Flask(__name__)

SERPAPI_KEY = "a3c6332180b59cd9845417aef8b4d95fb7d24adb4027da7a728ef07ec9b1fb88"
RAPIDAPI_KEY = "0a0c832913mshf933112d46406d6p147a81jsnc4dd15cf2fbe"
ADZUNA_APP_ID = "8857f5c6"
ADZUNA_APP_KEY = "2ac77f434f0c030404ff3a09cc4b5768"

def clean_and_extract_emails(text):
    if not text:
        return []
    raw_emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
    valid_emails = set()
    for em in raw_emails:
        em_clean = em.lower().strip()
        if not any(x in em_clean for x in ['.png', '.jpg', '.jpeg', 'example', 'sentry', 'w3.org', 'domain', 'email', '2x', '3x', 'bootstrap', 'vue', 'react']):
            valid_emails.add(em_clean)
    return list(valid_emails)

def fetch_serpapi(job, location, page):
    results = []
    try:
        url = "https://serpapi.com/search"
        start_from = (int(page) - 1) * 10
        params = {
            "engine": "google_jobs",
            "q": f"Ausbildung {job} {location} bewerbung email".strip(),
            "hl": "de",
            "gl": "de",
            "start": start_from,
            "api_key": SERPAPI_KEY
        }
        res = requests.get(url, params=params, timeout=6)
        if res.status_code == 200:
            jobs = res.json().get("jobs_results", [])
            for item in jobs:
                company = item.get("company_name", "مؤسسة صحية/ألمانية")
                title = item.get("title", job)
                desc = item.get("description", "") + " " + str(item.get("apply_options", ""))
                emails = clean_and_extract_emails(desc)
                for em in emails:
                    results.append((company, title, em, "Google Jobs"))
    except Exception:
        pass
    return results

def fetch_rapidapi(job, location, page):
    results = []
    try:
        url = "https://jsearch.p.rapidapi.com/search-v2"
        headers = {
            "x-rapidapi-host": "jsearch.p.rapidapi.com",
            "x-rapidapi-key": RAPIDAPI_KEY
        }
        params = {
            "query": f"Ausbildung {job} in {location} Germany email",
            "num_pages": "1",
            "page": str(page),
            "country": "de"
        }
        res = requests.get(url, headers=headers, params=params, timeout=6)
        if res.status_code == 200:
            data = res.json().get("data", [])
            for item in data:
                company = item.get("employer_name", "مؤسسة تدريب")
                title = item.get("job_title", job)
                desc = item.get("job_description", "")
                emails = clean_and_extract_emails(desc)
                for em in emails:
                    results.append((company, title, em, "JSearch API"))
    except Exception:
        pass
    return results

def fetch_adzuna(job, location, page):
    results = []
    try:
        url = f"https://api.adzuna.com/v1/api/jobs/de/search/{page}"
        params = {
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_APP_KEY,
            "what": f"Ausbildung {job}",
            "where": location,
            "results_per_page": 20
        }
        res = requests.get(url, params=params, timeout=6)
        if res.status_code == 200:
            jobs = res.json().get("results", [])
            for item in jobs:
                company = item.get("company", {}).get("display_name", "دار عجزة / مستشفى")
                title = item.get("title", job)
                desc = item.get("description", "")
                emails = clean_and_extract_emails(desc)
                for em in emails:
                    results.append((company, title, em, "Adzuna API"))
    except Exception:
        pass
    return results

@app.route('/', methods=['GET', 'POST'])
def index():
    all_results = []
    message = ""
    
    if request.method == 'POST':
        job = request.form.get('job', '').strip()
        location = request.form.get('location', '').strip()
        start_year = request.form.get('start_year', '2027').strip()
        page = request.form.get('page', '1').strip()
        
        found_set = set()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            f1 = executor.submit(fetch_serpapi, job, location, page)
            f2 = executor.submit(fetch_rapidapi, job, location, page)
            f3 = executor.submit(fetch_adzuna, job, location, page)
            
            for f in concurrent.futures.as_completed([f1, f2, f3]):
                for item in f.result():
                    found_set.add(item)

        for comp, tit, em, src in found_set:
            all_results.append({
                "company": comp,
                "title": tit,
                "email": em,
                "source": src,
                "year": start_year
            })

        if not all_results:
            message = "⚠️ لم يتم العثور على إيميلات في هذه الصفحة. جرب تغيير رقم الصفحة أو المدينة."

    html_template = '''
    <!doctype html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>محرك إيميلات الأوسبيلدونغ HR</title>
        <style>
            body { font-family: system-ui, -apple-system, sans-serif; background: #f8fafc; margin: 0; padding: 20px; color: #0f172a; }
            .card { max-width: 850px; margin: auto; background: white; padding: 30px; border-radius: 16px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05); }
            h2 { text-align: center; color: #1e3a8a; margin-bottom: 25px; }
            .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
            .full-width { grid-column: span 2; }
            label { display: block; margin-top: 10px; font-weight: 600; font-size: 14px; color: #334155; }
            input { width: 100%; padding: 12px; margin-top: 5px; border: 1px solid #cbd5e1; border-radius: 8px; box-sizing: border-box; font-size: 15px; }
            button { background: #059669; color: white; border: none; padding: 14px; width: 100%; margin-top: 20px; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 16px; transition: 0.2s; }
            button:hover { background: #047857; }
            .download-btn { background: #2563eb; display: block; text-align: center; color: white; padding: 12px; border-radius: 8px; margin-top: 15px; text-decoration: none; font-weight: bold; }
            .download-btn:hover { background: #1d4ed8; }
            .alert { background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; padding: 12px; border-radius: 8px; margin-top: 20px; text-align: center; }
            table { width: 100%; margin-top: 25px; border-collapse: collapse; font-size: 14px; }
            th, td { border: 1px solid #e2e8f0; padding: 12px; text-align: right; }
            th { background: #f1f5f9; color:

