# github_api.py
import json
import os
import re
import xml.etree.ElementTree as ET

import requests

from version_utils import compare_versions, normalize_version

CACHE_FILE = "latest_release_cache.json"
APP_CACHE_FILE = "app_release_cache.json"
ATOM_NS = {'atom': 'http://www.w3.org/2005/Atom'}


def _get_app_dir():
    """Папка приложения (рядом с exe или скриптами)."""
    import sys
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _cache_path(filename):
    return os.path.join(_get_app_dir(), filename)


def _fetch_rss(rss_url):
    """Загружает и парсит RSS-ленту релизов GitHub."""
    response = requests.get(rss_url, timeout=15)
    response.raise_for_status()
    return ET.fromstring(response.content)


def _extract_tag_from_link(link):
    """Извлекает тег релиза из URL вида .../releases/tag/1.10.1."""
    if '/tag/' not in link:
        return None
    return link.split('/tag/')[-1].strip()


def _extract_version_from_title(title):
    """Извлекает номер версии из заголовка релиза."""
    match = re.search(r'(\d+\.\d+\.\d+[a-zA-Z]?)', title or '')
    return match.group(1) if match else (title or '').strip()


def _verify_download_url(url):
    """Проверяет, что архив доступен для скачивания."""
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        return response.status_code == 200
    except requests.RequestException:
        return False


def _build_archive_url(repo, tag):
    """Формирует URL архива и проверяет доступность."""
    candidates = [
        f"https://github.com/{repo}/archive/refs/tags/{tag}.zip",
        f"https://github.com/{repo}/archive/{tag}.zip",
    ]

    if not tag.startswith('v'):
        candidates.append(
            f"https://github.com/{repo}/archive/refs/tags/v{tag}.zip"
        )

    for url in candidates:
        if _verify_download_url(url):
            return url

    return candidates[0]


def _parse_release_entries(root):
    """Извлекает все релизы из RSS-ленты."""
    entries = []

    for entry in root.findall('atom:entry', ATOM_NS):
        title_elem = entry.find('atom:title', ATOM_NS)
        link_elem = entry.find('atom:link', ATOM_NS)
        if title_elem is None or link_elem is None:
            continue

        title = title_elem.text or ''
        link = link_elem.get('href') or ''
        tag = _extract_tag_from_link(link) or _extract_version_from_title(title)
        if not tag:
            continue

        version = normalize_version(tag)
        entries.append({
            "version": version,
            "tag": tag,
            "html_url": link,
            "title": title,
        })

    return entries


def _pick_latest_entry(entries):
    """Выбирает релиз с наибольшим номером версии."""
    if not entries:
        return None

    latest = entries[0]
    for entry in entries[1:]:
        if compare_versions(entry['version'], latest['version']) > 0:
            latest = entry

    return latest


def get_latest_release(repo):
    """
    Получает последний релиз Zapret через RSS (работает без VPN).
    """
    rss_url = f"https://github.com/{repo}/releases.atom"

    try:
        root = _fetch_rss(rss_url)
        latest_entry = _pick_latest_entry(_parse_release_entries(root))

        if latest_entry is not None:
            tag = latest_entry['tag']
            version = latest_entry['version']

            result = {
                "version": version,
                "tag": tag,
                "download_url": _build_archive_url(repo, tag),
                "html_url": latest_entry['html_url'],
            }

            with open(_cache_path(CACHE_FILE), 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            print(f"✅ Получена версия {version} (тег: {tag}) через RSS")
            return result

    except Exception as e:
        print(f"⚠️ Не удалось подключиться к RSS: {e}")

    cache_file = _cache_path(CACHE_FILE)
    if os.path.exists(cache_file):
        print("📦 Использую кэшированные данные о релизе.")
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    print("❌ Нет данных о релизе. Проверьте интернет.")
    return None


def _find_exe_download_url(repo, version, release_page_url):
    """Ищет ссылку на .exe в HTML страницы релиза."""
    try:
        response = requests.get(
            release_page_url,
            timeout=15,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'},
        )
        if response.status_code != 200:
            return None

        pattern = rf'/{repo}/releases/download/{re.escape(version)}/([\w\-.]+\.exe)'
        match = re.search(pattern, response.text)
        if match:
            filename = match.group(1)
            url = f"https://github.com/{repo}/releases/download/{version}/{filename}"
            print(f"📦 Найден .exe файл: {filename}")
            return url
    except requests.RequestException as e:
        print(f"⚠️ Не удалось спарсить страницу релиза: {e}")

    return None


def _probe_exe_urls(repo, version):
    """Пробует стандартные имена .exe файлов."""
    possible_names = [
        "ZapretChecker.exe",
        "ZapretUpdater.exe",
        "zapret-checker.exe",
    ]

    for name in possible_names:
        url = f"https://github.com/{repo}/releases/download/{version}/{name}"
        if _verify_download_url(url):
            print(f"✅ Найден .exe файл: {name}")
            return url

    return None


def get_latest_app_release(repo):
    """
    Получает последний релиз приложения через RSS.
    """
    rss_url = f"https://github.com/{repo}/releases.atom"

    try:
        root = _fetch_rss(rss_url)
        latest_entry = _pick_latest_entry(_parse_release_entries(root))

        if latest_entry is not None:
            tag = latest_entry['tag']
            version = latest_entry['version']

            exe_url = _find_exe_download_url(repo, tag, latest_entry['html_url'])
            if not exe_url:
                exe_url = _probe_exe_urls(repo, tag)
            if not exe_url and tag.lstrip('v') != version:
                exe_url = _probe_exe_urls(repo, version)
            if not exe_url:
                exe_url = (
                    f"https://github.com/{repo}/releases/latest/download/ZapretChecker.exe"
                )
                print("⚠️ Использую стандартную ссылку: ZapretChecker.exe")

            result = {
                "version": version,
                "tag": tag,
                "download_url": exe_url,
                "html_url": latest_entry['html_url'],
            }

            with open(_cache_path(APP_CACHE_FILE), 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            print(f"✅ Получена версия приложения {version} через RSS")
            return result

    except Exception as e:
        print(f"⚠️ Не удалось подключиться к RSS приложения: {e}")

    cache_file = _cache_path(APP_CACHE_FILE)
    if os.path.exists(cache_file):
        print("📦 Использую кэшированные данные о релизе приложения.")
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    print("❌ Нет данных о релизе приложения.")
    return None
