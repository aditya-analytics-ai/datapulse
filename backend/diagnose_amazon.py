import sys
sys.stdout.reconfigure(encoding='utf-8')
from bs4 import BeautifulSoup

with open('deals_snippet.html', encoding='utf-8', errors='replace') as f:
    html = f.read()

soup = BeautifulSoup(html, 'lxml')

asins = [c for c in soup.select('[data-asin]') if c.get('data-asin','').strip()]
print(f'Total data-asin: {len(asins)}')

if asins:
    a = asins[0]
    print('ASIN:', a.get('data-asin'))
    print('Tag:', a.name)
    print('Classes:', a.get('class'))
    text = a.get_text(separator=' ', strip=True)
    print('Text:', text[:300])
    print()
    for child in list(a.children)[:8]:
        if hasattr(child, 'name') and child.name:
            ctext = child.get_text(strip=True)[:80]
            print('  Child:', child.name, child.get('class'), ctext)
