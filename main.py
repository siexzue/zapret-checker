# main.py
import os
import sys

sys.path.append(os.path.dirname(__file__))

from config import ARCHIVE_NAME, ZAPRET_REPO, get_zapret_path
from downloader import update_zapret
from github_api import get_latest_release
from local_version import get_local_version, update_version
from version_utils import compare_versions, is_update_available


def main():
    print("=" * 50)
    print("🚀 Zapret Auto Updater (Консольная версия)")
    print("=" * 50)

    zapret_path = get_zapret_path()
    if not zapret_path:
        zapret_path = input("Введите путь к папке Zapret: ").strip().strip('"')
        if not zapret_path:
            print("❌ Путь не указан.")
            return

    local_version = get_local_version(zapret_path)
    if local_version:
        print(f"📂 Установленная версия: {local_version}")
        print(f"📁 Путь: {zapret_path}")
    else:
        print(f"⚠️ Не удалось определить версию в папке: {zapret_path}")
        print("Убедитесь, что Zapret установлен корректно.")
        return

    latest = get_latest_release(ZAPRET_REPO)
    if not latest:
        print("❌ Не удалось получить информацию о релизе.")
        return

    latest_version = latest['version']
    print(f"🌐 Последняя версия на GitHub: {latest_version}")

    if not is_update_available(local_version, latest_version):
        if compare_versions(local_version, latest_version) > 0:
            print("ℹ️ Локальная версия новее, чем на GitHub.")
        else:
            print("✅ У вас актуальная версия. Обновление не требуется.")
        return

    print("🔥 ДОСТУПНО ОБНОВЛЕНИЕ!")
    print(f"   {local_version} → {latest_version}")
    print(f"Ссылка на релиз: {latest['html_url']}")

    choice = input("\nОбновить сейчас? (y/n): ").strip().lower()
    if choice != 'y':
        print("👋 До свидания!")
        return

    success = update_zapret(
        zapret_path=zapret_path,
        download_url=latest['download_url'],
        archive_name=ARCHIVE_NAME,
    )

    if success:
        update_version(latest_version)
        print(f"\n🎉 Zapret успешно обновлён до версии {latest_version}!")
    else:
        print("\n❌ Обновление не удалось.")


if __name__ == "__main__":
    main()
