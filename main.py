# main.py
import sys
import os
sys.path.append(os.path.dirname(__file__))

from config import GITHUB_REPO, ZAPRET_PATH, ARCHIVE_NAME
from github_api import get_latest_release
from local_version import get_local_version, update_version
from downloader import update_zapret

def main():
    print("=" * 50)
    print("🚀 Zapret Auto Updater (Консольная версия)")
    print("=" * 50)
    
    # Определяем локальную версию
    local_version = get_local_version(ZAPRET_PATH)
    if local_version:
        print(f"📂 Установленная версия: {local_version}")
        print(f"📁 Путь: {ZAPRET_PATH}")
    else:
        print(f"⚠️ Не удалось определить версию в папке: {ZAPRET_PATH}")
        print("Убедитесь, что Zapret установлен корректно.")
        return
    
    # Получаем информацию о последнем релизе
    latest = get_latest_release(GITHUB_REPO)
    if not latest:
        print("❌ Не удалось получить информацию о релизе.")
        return
    
    print(f"🌐 Последняя версия на GitHub: {latest['version']}")
    
    # Сравниваем версии
    if latest['version'] == local_version:
        print("✅ У вас актуальная версия. Обновление не требуется.")
        return
    
    print("🔥 ДОСТУПНО ОБНОВЛЕНИЕ!")
    print(f"Ссылка на релиз: {latest['html_url']}")
    
    # Спрашиваем, нужно ли обновляться
    choice = input("\nОбновить сейчас? (y/n): ").strip().lower()
    if choice != 'y':
        print("👋 До свидания!")
        return
    
    # Запускаем обновление
    success = update_zapret(
        zapret_path=ZAPRET_PATH,
        download_url=latest['download_url'],
        archive_name=ARCHIVE_NAME
    )
    
    if success:
        update_version(latest['version'])
        print(f"\n🎉 Zapret успешно обновлён до версии {latest['version']}!")
    else:
        print("\n❌ Обновление не удалось.")

if __name__ == "__main__":
    main()