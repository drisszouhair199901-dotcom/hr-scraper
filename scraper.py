
import os
import re
import requests
import csv
from flask import Flask, render_template_string, request

app = Flask(__name__)

# قائمة المواقع الرسمية المعتمدة للأوسبيلدونغ في ألمانيا
GERMAN_AUSBILDUNG_SITES = [
    "https://www.ausbildung.de/suche/?search={job}&location={location}",
    "https://www.azubiyo.de/ausbildung/{location}/{job}/",
    "https://www.arbeitsagentur.de/jobsuche/suche?geometrie={location}&was={job}",
    "https://www.stepstone.de/s1/ausbildung-{job}-{location}",
    "https://www.praktikum.de/stellenangebote?q={job}&l={location}",
    "https://www.jobware.de/arbeit/ausbildung-{job}-{location}",
    "https://www.kimeta.de/ausbildung-{job}-in-{location}"
]

# خريطة الأقاليم والولايات لتغطية المدن والمناطق المجاورة لها (Regional)
REGIONAL_MAP = {
    "stuttgart": "stuttgart-region",
    "münchen": "muenchen-umgebung",
    "berlin": "berlin-brandenburg",
    "köln": "koeln-bonn",
    "frankfurt": "frankfurt-rhein-main",
    "hamburg": "hamburg-metropolregion",
    "düsseldorf": "duesseldorf-rhein-ruhr"
}

@app.route('/', methods=['GET', 'POST'])
def index():
    emails_data = []
    message = ""
    
    if request.method == 'POST':
        job = request.form.get('job', '').strip().lower()
        search_type = request.form.get('search_type', 'city') # city / state / all
        location_input = request.form.get('location', '').strip().lower()
        start_year = request.form.get('start_year', '2027').strip()
        
        # تحديد النطاق الجغرافي للبحث
        search_locations = []
        if search_type == 'city' and location_input:
            search_locations.append(location_input)
            # إضافة المنطقة الإقليمية المجاورة للمدينة إن وجدت
            if location_input in REGIONAL_MAP:
                search_locations.append(REGIONAL_MAP[location_input])
        elif search_type == 'state' and location_input:
            search_locations.append(f"land-{location_input}")
        else:
            search_locations.append("deutschland")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        
        found_emails = set()
        # كلمات دلالية للتحقق من أن الإيميل حقيقي وخاص بمؤسسات التوظيف
        valid_hr_keywords = ['hr', 'karriere', 'bewerbung', 'jobs', 'kontakt', 'info', 'ausbildung', 'azubi', 'personal', 'pflege', 'klinik', 'senioren']

        for loc in search_locations:
            for site_template in GERMAN_AUSBILDUNG_SITES:
                url = site_template.format(job=job, location=loc)
                try:
                    response = requests.get(url, headers=headers, timeout=8)
                    if response.status_code == 200:
                        # استخراج الإيميلات بدقة من محتوى الصفحة الحقيقي
                        extracted_emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', response.text)
                        for email in extracted_emails:
                            email_clean = email.lower().strip()
                            
                            # التصفية الصارمة: استبعاد الرموز والملفات التقنية
                            invalid_rules = ['.png', '.jpg', '.svg', '.webp', '.js', '.css', 'example', 'sentry', 'optimizely', 'webpack', 'github']
                            if any(rule in email_clean for rule in invalid_rules):
                                continue
                            
                            # الشرط الأساسي: الإيميل حقيقي ويتطابق مع معايير المؤسسات الألمانية
                            if any(kw in email_clean for kw in valid_hr_keywords) or email_clean.endswith('.de'):
                                found_emails.add((email_clean, loc, url))
                except Exception:
                    continue

        if found_emails:
            for email, loc, source in found_emails:
                emails_data.append({
                    "email": email, 
                    "job": job, 
                    "location": loc, 
                    "year": start_year, 
                    "source": source
                })
        else:
            message = f"⚠️ لم يتم العثور على أي إيميلات حقيقية وموثوقة في منطقة ({location_input}) بالنسبة لمهنة ({job}). جرب البحث في ولاية كاملة أو مدينة مجاورة."

    html_template = '''
    <!doctype html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>محرك استخراج إيميلات الأوسبيلدونغ - ألمانيا</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #eef2f5; margin: 0; padding: 15px; color: #2c3e50; }
            .card { max-width: 650px; margin: auto; background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
            h2 { text-align: center; color: #1a365d; margin-bottom: 20px; }
            label { display: block; margin-top: 12px; font-weight: 600; font-size: 14px; }
            input, select { width: 100%; padding: 11px; margin-top: 5px; border: 1px solid #cbd5e1; border-radius: 8px; box-sizing: border-box; font-size: 15px; }
            button { background: #2563eb; color: white; border: none; padding: 13px; width: 100%; margin-top: 20px; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; transition: 0.2s; }
            button:hover { background: #1d4ed8; }
            .alert { background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; padding: 12px; border-radius: 8px; margin-top: 20px; text-align: center; font-size: 14px; }
            table { width: 100%; margin-top: 20px; border-collapse: collapse; font-size: 13px; }
            th, td { border: 1px solid #e2e8f0; padding: 10px; text-align: right; }
            th { background: #f8fafc; color: #475569; }
            .badge { background: #dbeafe; color: #1e40af; padding: 3px 7px; border-radius: 4px; font-size: 11px; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>🇩🇪 محرك إيميلات الأوسبيلدونغ المعتمد</h2>
            <form method="POST">
                <label>نوع التكوين المهني (Ausbildung):</label>
                <input type="text" name="job" placeholder="مثال: pflegefachmann" value="{{ request.form.get('job', 'pflegefachmann') }}" required>

                <label>نطاق البحث الجغرافي:</label>
                <select name="search_type">
                    <option value="city" {% if request.form.get('search_type') == 'city' %}selected{% endif %}>مدينة محددة + إقليمها المكتظ (Regional)</option>
                    <option value="state" {% if request.form.get('search_type') == 'state' %}selected{% endif %}>ولاية كاملة (Bundesland)</option>
                    <option value="all" {% if request.form.get('search_type') == 'all' %}selected{% endif %}>ألمانيا كاملة</option>
                </select>

                <label>اسم المدينة أو الولاية (بالألمانية):</label>
                <input type="text" name="location" placeholder="مثال: stuttgart أو bayern" value="{{ request.form.get('location', 'stuttgart') }}">

                <label>سنة البدء المطلوبة:</label>
                <input type="text" name="start_year" value="{{ request.form.get('start_year', '2027') }}" required>

                <button type="submit">بدء التفتيش والجلب الحقيقي 🔍</button>
            </form>

            {% if message %}
                <div class="alert">{{ message }}</div>
            {% endif %}

            {% if emails_data %}
                <h3 style="margin-top: 25px;">الإيميلات الحقيقية المستخرجة ({{ emails_data|length }}):</h3>
                <table>
                    <tr>
                        <th>البريد الإلكتروني</th>
                        <th>المنطقة / المصدر</th>
                    </tr>
                    {% for item in emails_data %}
                    <tr>
                        <td><a href="mailto:{{ item.email }}">{{ item.email }}</a></td>
                        <td><span class="badge">{{ item.location }}</span><br><small><a href="{{ item.source }}" target="_blank">رابط العرض</a></small></td>
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
