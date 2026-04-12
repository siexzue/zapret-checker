# github_api.py
import requests
import json
import os

CACHE_FILE = "latest_release_cache.json"

def get_latest_release(repo):
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            # Ищем .zip архив среди assets
            download_url = None
            for asset in data.get("assets", []):
                if asset["name"].endswith(".zip"):
                    download_url = asset["browser_download_url"]
                    break
            
            # Если архива нет в assets — используем zipball (архив исходников)
            if not download_url:
                download_url = data["zipball_url"]
            
            result = {
                "version": data["tag_name"],
                "download_url": download_url,
                "html_url": data["html_url"]
            }
            
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(result, f)
            print("✅ Данные получены с GitHub")
            return result
    except Exception as e:
        print(f"⚠️ Не удалось подключиться к GitHub: {e}")
    
    if os.path.exists(CACHE_FILE):
        print("📦 Использую кэшированные данные о релизе.")
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    print("❌ Нет данных о релизе. Проверьте интернет.")
    return None