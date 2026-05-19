import requests
from bs4 import BeautifulSoup
import json
import time
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def scrape_all_quotes():
    base_url = "http://quotes.toscrape.com/page/{}/"
    all_quotes = []
    page = 1
    while True:
        url = base_url.format(page)
        logger.info(f"Загрузка страницы {page}...")
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                break
            soup = BeautifulSoup(response.text, 'html.parser')
            quote_blocks = soup.find_all('div', class_='quote')
            if not quote_blocks:
                break
            for block in quote_blocks:
                text = block.find('span', class_='text').text
                author = block.find('small', class_='author').text
                tags = [tag.text for tag in block.find_all('a', class_='tag')]
                all_quotes.append({
                    'text': text,
                    'author': author,
                    'tags': tags
                })
            logger.info(f"Найдено {len(quote_blocks)} цитат")
            page += 1
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"Ошибка на странице {page}: {e}")
            break

    data_dir = Path(__file__).parent.parent / 'data'
    data_dir.mkdir(exist_ok=True)
    file_path = data_dir / 'quotes.json'
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(all_quotes, f, ensure_ascii=False, indent=2)
    logger.info(f"Готово. Сохранено {len(all_quotes)} цитат в {file_path}")

if __name__ == "__main__":
    scrape_all_quotes()