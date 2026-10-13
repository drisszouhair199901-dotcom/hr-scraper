import re
import requests
import csv

def scrape_emails():
    # روابط المواقع أو صفحات البحث المستهدفة في ألمانيا
    urls = [
        "https://www.stepstone.de/jobs/pflegefachmann/stuttgart",
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    found_emails = set()

    for url in urls:
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', response.text)
                for email in emails:
                    if not any(ext in email for ext in ['.png', '.jpg', '.svg', 'example.com']):
                        found_emails.add(email)
        except Exception as e:
            print(f"Error: {e}")

    # حفظ النتائج في ملف CSV
    with open('hr_emails.csv', mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Email"])
        for email in found_emails:
            writer.writerow([email])
            
    print(f"Saved {len(found_emails)} emails.")

if __name__ == "__main__":
    scrape_emails()
