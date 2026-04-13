# github_api.py
import requests
import json
import os
import re
import xml.etree.ElementTree as ET

CACHE_FILE = "latest_release_cache.json"
APP_CACHE_FILE = "app_release_cache.json"


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


def get_latest_app_release(repo):
    """
    Получает последний релиз приложения через RSS + парсинг страницы (работает без VPN!)
    """
    rss_url = f"https://github.com/{repo}/releases.atom"

    try:
        response = requests.get(rss_url, timeout=10)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            entry = root.find('atom:entry', ns)

            if entry is not None:
                title = entry.find('atom:title', ns).text
                link = entry.find('atom:link', ns).get('href')

                # Получаем версию из ссылки (тег релиза)
                version = None
                if '/tag/' in link:
                    version = link.split('/tag/')[-1].strip()

                # Если не получилось — ищем в title
                if not version:
                    version_match = re.search(r'(\d+\.\d+\.\d+[a-z]?)', title)
                    version = version_match.group(1) if version_match else title

                # Пытаемся найти .exe файл через парсинг страницы релиза
                exe_download_url = None
                try:
                    page_response = requests.get(link, timeout=10, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    if page_response.status_code == 200:
                        # Ищем ссылки на .exe файлы
                        html = page_response.text
                        # Паттерн: /user/repo/releases/download/tag/filename.exe
                        exe_match = re.search(
                            rf'/{repo}/releases/download/{re.escape(version)}/([\w\-]+\.exe)',
                            html
                        )
                        if exe_match:
                            filename = exe_match.group(1)
                            exe_download_url = f"https://github.com/{repo}/releases/download/{version}/{filename}"
                            print(f"📦 Найден .exe файл: {filename}")
                except Exception as e:
                    print(f"⚠️ Не удалось спарсить страницу релиза: {e}")

                # Если не нашли — пробуем стандартные варианты
                if not exe_download_url:
                    print("⚠️ Не удалось найти .exe файл, пробую стандартные имена...")
                    # Пробуем разные варианты имени
                    possible_names = [
                        "zapret-checker.exe",
                        "ZapretChecker.exe",
                        "ZapretUpdater.exe",
                        "main.exe",
                        "app.exe"
                    ]
                    
                    for name in possible_names:
                        test_url = f"https://github.com/{repo}/releases/download/{version}/{name}"
                        try:
                            test_resp = requests.head(test_url, timeout=5, allow_redirects=True)
                            if test_resp.status_code == 200:
                                exe_download_url = test_url
                                print(f"✅ Найден .exe файл: {name}")
                                break
                        except:
                            continue

                # Если всё ещё не нашли — используем latest/download
                if not exe_download_url:
                    exe_download_url = f"https://github.com/{repo}/releases/latest/download/zapret-checker.exe"
                    print(f"⚠️ Использую стандартную ссылку: zapret-checker.exe")

                result = {
                    "version": version,
                    "download_url": exe_download_url,
                    "html_url": link
                }

                # Сохраняем в кэш
                with open(APP_CACHE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(result, f)

                print(f"✅ Получена версия приложения {version} через RSS")
                return result

    except Exception as e:
        print(f"⚠️ Не удалось подключиться к RSS приложения: {e}")

    # Пробуем кэш
    if os.path.exists(APP_CACHE_FILE):
        print("📦 Использую кэшированные данные о релизе приложения.")
        with open(APP_CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    print("❌ Нет данных о релизе приложения.")
    return None