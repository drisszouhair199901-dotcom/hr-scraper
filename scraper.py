import os
import re
import concurrent.futures
import requests
from flask import Flask, render_template_string, request

app = Flask(__name__)

# المفاتيح الخاصة بك المدمجة جاهزة
SERPAPI_KEY = "a3c6332180b59cd9845417aef8b4d95fb7d24adb4027da7a728ef07ec9b1fb88"
RAPIDAPI_KEY = "0a0c832913mshf933112d46406d6p147a81jsnc4dd15cf2fbe"
ADZUNA_APP_ID = "8857f5c6"
ADZUNA_APP_KEY = "2ac77f434f0c030404ff3a09cc4b5768"

def fetch_serpapi(job, location):
    results = []
    try:
        url = "https://serpapi.com/search"
        params = {
            "engine": "google_jobs",
            "q": f"Ausbildung {job} {location}".strip(),
            "hl": "de",
            "gl": "de",
            "api_key": SERPAPI_KEY
        }
        res = requests.get(url, params=params, timeout=6)
        if res.status_code == 200:
            jobs = res.json().get("jobs_results", [])
            for item in jobs:
                company = item.get("company_name", "مؤسسة ألمانية")
                title = item.get("title", job)
                desc = item.get("description", "")
                emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', desc)
                email = emails[0] if emails else "تواصل مع المؤسسة"
                apply_links = item.get("apply_options", [])
                link = apply_links[0].get("link") if apply_links else "https://www.ausbildung.de"
                results.append((company, title, email, link, "Google Jobs (SerpApi)"))
    except Exception:
        pass
    return results

def fetch_rapidapi(job, location):
    results = []
    try:
        url = "https://jsearch.p.rapidapi.com/search-v2"
        headers = {
            "x-rapidapi-host": "jsearch.p.rapidapi.com",
            "x-rapidapi-key": RAPIDAPI_KEY
        }
        params = {
            "query": f"Ausbildung {job} in {location} Germany",
            "num_pages": "1",
            "country": "de"
        }
        res = requests.get(url, headers=headers, params=params, timeout=6)
        if res.status_code == 200:
            data = res.json().get("data", [])
            for item in data:
                company = item.get("employer_name", "شركة ألمانية")
                title = item.get("job_title", job)
                desc = item.get("job_description", "")
                emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', desc)
                email = emails[0] if emails else "تواصل عبر الرابط"
                link = item.get("job_apply_link") or "https://www.google.com"
                results.append((company, title, email, link, "JSearch (RapidAPI)"))
    except Exception:
        pass
    return results

def fetch_adzuna(job, location):
    results = []
    try:
        url = f"https://api.adzuna.com/v1/api/jobs/de/search/1"
        params = {
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_APP_KEY,
            "what": f"Ausbildung {job}",
            "where": location,
            "results_per_page": 10
        }
        res = requests.get(url, params=params, timeout=6)
        if res.status_code == 200:
            jobs = res.json().get("results", [])
            for item in jobs:
                company = item.get("company", {}).get("display_name", "مؤسسة ألمانية")
                title = item.get("title", job)
                desc = item.get("description", "")
                emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', desc)
                email = emails[0] if emails else "تقديم مباشر"
                link = item.get("redirect_url", "https://www.adzuna.de")
                results.append((company, title, email, link, "Adzuna Germany"))
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
        
        found_set = set()
        
        # تشغيل المحركات بالتوازي لتفادي الـ Timeout على Vercel
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            f1 = executor.submit(fetch_serpapi, job, location)
            f2 = executor.submit(fetch_rapidapi, job, location)
            f3 = executor.submit(fetch_adzuna, job, location)
            
            for f in concurrent.futures.as_completed([f1, f2, f3]):
                for item in f.result():
                    found_set.add(item)

        for comp, tit, em, ln, src in found_set:
            all_results.append({
                "company": comp,
                "title": tit,
                "email": em,
                "link": ln,
                "source": src,
                "year": start_year
            })

        if not all_results:
            message = "⚠️ لم يتم العثور على نتائج كافية. جرب تغيير المدينة أو اسم التكوين (مثال: Pflegefachmann / Stuttgart)."

    html_template = '''
    <!doctype html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>المحرك الشامل للأوسبيلدونغ</title>
        <style>
            body { font-family: system-ui, -apple-system, sans-serif; background: #f8fafc; margin: 0; padding: 20px; color: #0f172a; }
            .card { max-width: 850px; margin: auto; background: white; padding: 30px; border-radius: 16px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05); }
            h2 { text-align: center; color: #1e3a8a; margin-bottom: 25px; }
            label { display: block; margin-top: 15px; font-weight: 600; font-size: 14px; color: #334155; }
            input { width: 100%; padding: 12px; margin-top: 6px; border: 1px solid #cbd5e1; border-radius: 8px; box-sizing: border-box; font-size: 15px; }
            button { background: #2563eb; color: white; border: none; padding: 14px; width: 100%; margin-top: 25px; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 16px; transition: 0.2s; }
            button:hover { background: #1d4ed8; }
            .alert { background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; padding: 12px; border-radius: 8px; margin-top: 20px; text-align: center; }
            table { width: 100%; margin-top: 25px; border-collapse: collapse; font-size: 14px; }
            th, td { border: 1px solid #e2e8f0; padding: 12px; text-align: right; }
            th { background: #f1f5f9; color: #475569; }
            .badge { background: #e0e7ff; color: #3730a3; padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: 600; }
            a { color: #2563eb; text-decoration: none; font-weight: bold; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>🇩🇪 محرك الأوسبيلدونغ الشامل (Multi-API Engine)</h2>
            <form method="POST">
                <label>نوع التكوين المهني (Ausbildung):</label>
                <input type="text" name="job" placeholder="مثال: Pflegefachmann" value="{{ request.form.get('job', 'Pflegefachmann') }}" required>

                <label>المدينة أو الولاية بألمانيا:</label>
                <input type="text" name="location" placeholder="مثال: Stuttgart" value="{{ request.form.get('location', 'Stuttgart') }}" required>

                <label>سنة البدء المطلوبة:</label>
                <input type="text" name="start_year" value="{{ request.form.get('start_year', '2027') }}" required>

                <button type="submit">بحث شامل في جميع المصادر 🚀</button>
            </form>

            {% if message %}<div class="alert">{{ message }}</div>{% endif %}

            {% if all_results %}
                <h3 style="margin-top: 30px;">النتائج المجمعة من كافة المصادر ({{ all_results|length }} فرصة):</h3>
                <table>
                    <tr>
                        <th>المؤسسة / التخصص</th>
                        <th>البريد أو رابط التقديم</th>
                        <th>المصدر</th>
                    </tr>
                    {% for item in all_results %}
                    <tr>
                        <td><b>{{ item.company }}</b><br><small style="color: #64748b;">{{ item.title }} (سنة {{ item.year }})</small></td>
                        <td>
                            {% if '@' in item.email %}
                                <a href="mailto:{{ item.email }}">{{ item.email }}</a>
                            {% else %}
                                <a href="{{ item.link }}" target="_blank">رابط التقديم المباشر 🔗</a>
                            {% endif %}
                        </td>
                        <td><span class="badge">{{ item.source }}</span></td>
                    </tr>
                    {% endfor %}
                </table>
            {% endif %}
        </div>
    </body>
    </html>
    '''
    return render_template_string(html_template, all_results=all_results, message=message)

if __name__ == '__main__':
    app.run(debug=True)

