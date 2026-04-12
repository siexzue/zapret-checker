# main.py
from config import GITHUB_REPO, CURRENT_VERSION
from github_api import get_latest_release

def main():
    print("=== Zapret Auto Updater ===")
    print(f"Проверяю репозиторий: {GITHUB_REPO}")
    print(f"Текущая версия: {CURRENT_VERSION}")
    
    latest = get_latest_release(GITHUB_REPO)
    if latest:
        print(f"Последняя версия: {latest['version']}")
        if latest['version'] != CURRENT_VERSION:
            print("Доступно обновление!")
        else:
            print("У вас актуальная версия.")
    else:
        print("Не удалось получить информацию о релизе.")

if __name__ == "__main__":
    main()