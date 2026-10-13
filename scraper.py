import os
import re
import requests
import csv

def scrape_emails():
    # قراءة المدخلات التي كتبتها في الواجهة
    job_title = os.environ.get('JOB_TITLE', 'pflegefachmann').strip().lower()
    location = os.environ.get('LOCATION', 'stuttgart').strip().lower()
    start_year = os.environ.get('START_YEAR', '2027').strip()
    
    print(f"Searching for: Job={job_title}, Location={location}, Year={start_year}")

    urls = []
    
    # إذا اخترت البحث في ألمانيا كاملة أو مدينة محددة
    if location == "alle" or location == "الكل":
        urls.append(f"https://www.stepstone.de/jobs/{job_title}")
    else:
        urls.append(f"https://www.stepstone.de/jobs/{job_title}/in-{location}")
        
    # يمكنك إضافة منصات أخرى معتمدة هنا بنفس الطريقة
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    found_emails = set()

    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', response.text)
                for email in emails:
                    if not any(ext in email.lower() for ext in ['.png', '.jpg', '.jpeg', '.svg', '.webp', 'example.com', 'sentry.io']):
                        found_emails.add(email)
        except Exception as e:
            print(f"Error fetching {url}: {e}")

    # حفظ النتائج في ملف CSV مع تدوين تفاصيل البحث لتعرف الإيميلات تخص أي مدينة
    with open('hr_emails.csv', mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Email", "Job", "Location", "Start Year"])
        for email in found_emails:
            writer.writerow([email, job_title, location, start_year])
            
    print(f"Saved {len(found_emails)} emails successfully.")

if __name__ == "__main__":
    scrape_emails()
