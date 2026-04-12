# github_api.py
import requests
import json
import os
import xml.etree.ElementTree as ET

CACHE_FILE = "latest_release_cache.json"

def get_latest_release(repo):
    """
    Получает последний релиз через RSS-ленту (работает без VPN!)
    """
    # RSS-лента релизов (не заблокирована)
    rss_url = f"https://github.com/{repo}/releases.atom"
    
    try:
        response = requests.get(rss_url, timeout=10)
        if response.status_code == 200:
            # Парсим XML
            root = ET.fromstring(response.content)
            
            # Ищем первый entry (последний релиз)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            entry = root.find('atom:entry', ns)
            
            if entry is not None:
                title = entry.find('atom:title', ns).text
                link = entry.find('atom:link', ns).get('href')
                
                # Вытаскиваем версию из title (обычно "Release 1.9.7b")
                import re
                version_match = re.search(r'(\d+\.\d+\.\d+[a-z]?)', title)
                version = version_match.group(1) if version_match else title
                
                # Формируем ссылку на скачивание
                download_url = f"https://github.com/{repo}/archive/refs/tags/{version}.zip"
                
                result = {
                    "version": version,
                    "download_url": download_url,
                    "html_url": link
                }
                
                # Сохраняем в кэш
                with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(result, f)
                
                print(f"✅ Получена версия {version} через RSS")
                return result
                
    except Exception as e:
        print(f"⚠️ Не удалось подключиться к RSS: {e}")
    
    # Если RSS не сработал — пробуем кэш
    if os.path.exists(CACHE_FILE):
        print("📦 Использую кэшированные данные о релизе.")
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    print("❌ Нет данных о релизе. Проверьте интернет.")
    return None