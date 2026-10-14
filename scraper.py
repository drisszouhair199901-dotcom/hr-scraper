import os
import re
import requests
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, render_template_string, request

app = Flask(__name__)

# دالة سريعة لفحص رابط واحد واستخراج الإيميلات
def fetch_emails_from_url(url, headers):
    emails_found = set()
    try:
        res = requests.get(url, headers=headers, timeout=3)
        if res.status_code == 200:
            raw_emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', res.text)
            for email in raw_emails:
                clean = email.lower().strip()
                invalid = ['.png', '.jpg', '.svg', '.webp', '.js', '.css', 'example', 'sentry', 'optimizely', 'github', 'w3.org', 'google', 'domain']
                if not any(inv in clean for inv in invalid) and (clean.endswith('.de') or clean.endswith('.com')):
                    emails_found.add((clean, url))
    except Exception:
        pass
    return emails_found

@app.route('/', methods=['GET', 'POST'])
def index():
    emails_data = []
    message = ""
    
    if request.method == 'POST':
        job = request.form.get('job', '').strip().lower()
        search_type = request.form.get('search_type', 'city')
        location = request.form.get('location', '').strip().lower()
        start_year = request.form.get('start_year', '2027').strip()
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "de-DE,de;q=0.9,en;q=0.8"
        }
        
        loc_query = location if location else "deutschland"
        
        # استعلامات بحث فائقة السرعة والتركيز
        queries = [
            f"{job} ausbildung {loc_query} bewerbung email",
            f"site:ausbildung.de {job} {loc_query}",
            f"site:azubiyo.de {job} {loc_query}",
            f"site:stepstone.de ausbildung {job} {loc_query}",
            f"pflegeheim krankenhaus ausbildung {job} {loc_query} kontakt" if 'pflege' in job else f"{job} karriere {loc_query} kontakt email"
        ]

        target_links = set()
        
        # جلب الروابط بسرعة
        for q in queries:
            try:
                search_url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(q)}"
                resp = requests.post(search_url, headers=headers, timeout=3)
                if resp.status_code == 200:
                    links = re.findall(r'href="([^"]+)"', resp.text)
                    for l in links:
                        if "uddg=" in l:
                            url_clean = requests.utils.unquote(l.split("uddg=")[1].split("&")[0])
                            target_links.add(url_clean)
            except Exception:
                continue

        # فحص جميع الروابط بالتوازي (Parallel) لإنهاء العملية في ثوانٍ معدودة
        found_emails = set()
        urls_to_check = list(target_links)[:20]
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(lambda u: fetch_emails_from_url(u, headers), urls_to_check)
            for res in results:
                found_emails.update(res)

        if found_emails:
            for email, source in found_emails:
                emails_data.append({
                    "email": email,
                    "job": job,
                    "location": loc_query,
                    "year": start_year,
                    "source": source
                })
        else:
            message = f"⚠️ لم يتم العثور على إيميلات في ({loc_query}). جرب البحث عن مهنة أخرى أو كتابة الاسم بالألمانية (مثال: Berlin أو Bayern)."

    html_template = '''
    <!doctype html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>محرك إيميلات الأوسبيلدونغ السريع</title>
        <style>
            body { font-family: Tahoma, sans-serif; background: #eef2f5; margin: 0; padding: 15px; color: #2c3e50; }
            .card { max-width: 700px; margin: auto; background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
            h2 { text-align: center; color: #1a365d; }
            label { display: block; margin-top: 12px; font-weight: bold; }
            input, select { width: 100%; padding: 11px; margin-top: 5px; border: 1px solid #cbd5e1; border-radius: 8px; box-sizing: border-box; }
            button { background: #2563eb; color: white; border: none; padding: 13px; width: 100%; margin-top: 20px; border-radius: 8px; font-weight: bold; cursor: pointer; }
            button:hover { background: #1d4ed8; }
            .alert { background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; padding: 12px; border-radius: 8px; margin-top: 20px; text-align: center; font-size: 13px; }
            table { width: 100%; margin-top: 20px; border-collapse: collapse; font-size: 13px; }
            th, td { border: 1px solid #e2e8f0; padding: 10px; text-align: right; }
            th { background: #f8fafc; }
            .badge { background: #dbeafe; color: #1e40af; padding: 3px 7px; border-radius: 4px; font-size: 11px; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>🇩🇪 محرك إيميلات الأوسبيلدونغ (الفحص السريع)</h2>
            <form method="POST">
                <label>نوع التكوين المهني (Ausbildung):</label>
                <input type="text" name="job" placeholder="مثال: pflegefachmann" value="{{ request.form.get('job', 'pflegefachmann') }}" required>

                <label>نطاق البحث الجغرافي:</label>
                <select name="search_type">
                    <option value="city">مدينة محددة</option>
                    <option value="state">ولاية كاملة</option>
                    <option value="all">ألمانيا كاملة</option>
                </select>

                <label>اسم المدينة أو الولاية (بالألمانية):</label>
                <input type="text" name="location" placeholder="مثال: berlin أو bayern" value="{{ request.form.get('location', 'berlin') }}">

                <label>سنة البدء المطلوبة:</label>
                <input type="text" name="start_year" value="{{ request.form.get('start_year', '2027') }}" required>

                <button type="submit">بدء الفحص السريع 🚀</button>
            </form>

            {% if message %}<div class="alert">{{ message }}</div>{% endif %}

            {% if emails_data %}
                <h3 style="margin-top: 25px;">النتائج المستخرجة ({{ emails_data|length }} إيميل):</h3>
                <table>
                    <tr><th>البريد الإلكتروني</th><th>التفاصيل والمصدر</th></tr>
                    {% for item in emails_data %}
                    <tr>
                        <td><a href="mailto:{{ item.email }}">{{ item.email }}</a></td>
                        <td><span class="badge">{{ item.job }} - {{ item.location }} ({{ item.year }})</span><br><small><a href="{{ item.source }}" target="_blank">زيارة المصدر</a></small></td>
                    </tr>
                    {% endfor %}
                </table>
            {% endif %}
        </div>
    </body>
    </html>
    '''
    return render_template_string(html_template, emails_data=emails_data, message=message)

if __name__ == '__main__':
    app.run(debug=True)
