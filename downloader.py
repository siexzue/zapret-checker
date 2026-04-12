# downloader.py (обновлённая функция update_zapret)
import os
import shutil
import zipfile
import requests
import time

def download_file(url, save_path):
    print(f"📥 Скачиваю: {url}")
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(save_path, 'wb') as f:
        downloaded = 0
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded += len(chunk)
            if total_size > 0:
                percent = (downloaded / total_size) * 100
                print(f"\rПрогресс: {percent:.1f}%", end='')
    print("\n✅ Скачивание завершено!")

def extract_zip(zip_path, extract_to):
    print(f"📦 Распаковываю в: {extract_to}")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print("✅ Распаковка завершена!")

def update_zapret(zapret_path, download_url, archive_name):
    os.makedirs("downloads", exist_ok=True)
    zip_path = os.path.join("downloads", archive_name)
    
    download_file(download_url, zip_path)
    
    print(f"\n⚠️ ВНИМАНИЕ! Будет удалена папка: {zapret_path}")
    confirm = input("Продолжить? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Отмена.")
        return False
    
    # Пытаемся удалить старую папку
    if os.path.exists(zapret_path):
        print(f"🗑️ Удаляю старую версию: {zapret_path}")
        try:
            shutil.rmtree(zapret_path)
        except PermissionError:
            print("\n" + "=" * 50)
            print("❌ ОШИБКА: Не удалось удалить папку!")
            print("=" * 50)
            print("\n🔍 Возможные причины:")
            print("   • Zapret всё ещё запущен (проверьте трей/диспетчер задач)")
            print("   • Файлы используются другой программой")
            print("   • Недостаточно прав (попробуйте запустить от Администратора)")
            print("\n🛠️ Что делать:")
            print(f"   1. Закройте все программы, связанные с Zapret")
            print(f"   2. Удалите папку вручную: {zapret_path}")
            print(f"   3. Запустите программу ещё раз")
            print("=" * 50)
            return False
        except Exception as e:
            print(f"❌ Неизвестная ошибка при удалении: {e}")
            return False
    
    # Распаковываем новую версию
    try:
        extract_zip(zip_path, zapret_path)
    except Exception as e:
        print(f"❌ Ошибка при распаковке: {e}")
        return False
    
    print("✅ Обновление завершено!")
    return True