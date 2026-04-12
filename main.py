# main.py
from config import GITHUB_REPO, CURRENT_VERSION
from github_api import get_latest_release

def main():
    print("=== Zapret Auto Updater ===")
    print(f"Проверяю репозиторий: {GITHUB_REPO}")
    print(f"Текущая версия: {CURRENT_VERSION}")
    
    latest = get_latest_release(GITHUB_REPO)
    
    if latest:
        print(f"Последняя версия на GitHub: {latest['version']}")
        
        if latest['version'] != CURRENT_VERSION:
            print("🔥 ДОСТУПНО ОБНОВЛЕНИЕ!")
            print(f"Скачать можно тут: {latest['html_url']}")
        else:
            print("✅ У вас актуальная версия.")
    else:
        print("❌ Не удалось проверить обновления.")
        print("Программа продолжит работу с текущей версией.")

if __name__ == "__main__":
    main()