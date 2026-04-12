# downloader.py
import os
import shutil
import zipfile
import requests
import time

def download_file(url, save_path, log_callback=None):
    """Скачивает файл по URL."""
    msg = f"📥 Скачиваю: {url}"
    if log_callback:
        log_callback(msg)
    else:
        print(msg)
    
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(save_path, 'wb') as f:
        downloaded = 0
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded += len(chunk)
            if total_size > 0 and not log_callback:
                percent = (downloaded / total_size) * 100
                print(f"\rПрогресс: {percent:.1f}%", end='')
    
    msg = "\n✅ Скачивание завершено!" if not log_callback else "✅ Скачивание завершено!"
    if log_callback:
        log_callback(msg)
    else:
        print(msg)

def extract_zip(zip_path, extract_to):
    """Распаковывает ZIP архив, извлекая содержимое без вложенной папки."""
    print(f"📦 Распаковываю в: {extract_to}")
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        all_files = zip_ref.namelist()
        
        if all_files:
            root_folder = all_files[0].split('/')[0]
            
            for file in all_files:
                # Пропускаем папки .github (они не нужны для работы Zapret)
                if '.github' in file:
                    continue
                    
                if file.startswith(root_folder + '/'):
                    target_path = file[len(root_folder) + 1:]
                else:
                    target_path = file
                
                if target_path:
                    full_path = os.path.join(extract_to, target_path)
                    
                    # Создаём папки
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    
                    # Извлекаем ТОЛЬКО файлы (не папки)
                    if not file.endswith('/'):
                        with zip_ref.open(file) as source, open(full_path, 'wb') as target:
                            target.write(source.read())
    
    print("✅ Распаковка завершена!")

def update_zapret(zapret_path, download_url, archive_name, skip_confirm=False, log_callback=None):
    """Обновляет Zapret."""
    os.makedirs("downloads", exist_ok=True)
    zip_path = os.path.join("downloads", archive_name)
    
    download_file(download_url, zip_path, log_callback)
    
    if not skip_confirm:
        print(f"\n⚠️ ВНИМАНИЕ! Будет удалена папка: {zapret_path}")
        confirm = input("Продолжить? (y/n): ").strip().lower()
        if confirm != 'y':
            if log_callback:
                log_callback("❌ Отмена пользователем.")
            else:
                print("❌ Отмена.")
            return False
    
    if os.path.exists(zapret_path):
        msg = f"🗑️ Удаляю старую версию: {zapret_path}"
        if log_callback:
            log_callback(msg)
        else:
            print(msg)
        
        try:
            shutil.rmtree(zapret_path)
        except PermissionError:
            error_msg = (
                "\n" + "=" * 50 + "\n"
                "❌ ОШИБКА: Не удалось удалить папку!\n"
                "=" * 50 + "\n"
                "\n🔍 Возможные причины:\n"
                "   • Zapret всё ещё запущен\n"
                "   • Файлы используются другой программой\n"
                "   • Недостаточно прав\n"
                "\n🛠️ Что делать:\n"
                f"   1. Закройте Zapret\n"
                f"   2. Удалите папку вручную: {zapret_path}\n"
                "   3. Запустите программу ещё раз\n"
                "=" * 50
            )
            if log_callback:
                log_callback(error_msg)
            else:
                print(error_msg)
            return False
        except Exception as e:
            error_msg = f"❌ Неизвестная ошибка при удалении: {e}"
            if log_callback:
                log_callback(error_msg)
            else:
                print(error_msg)
            return False
    
    try:
        extract_zip(zip_path, zapret_path)
    except Exception as e:
        error_msg = f"❌ Ошибка при распаковке: {e}"
        if log_callback:
            log_callback(error_msg)
        else:
            print(error_msg)
        return False
    
    success_msg = "✅ Обновление завершено!"
    if log_callback:
        log_callback(success_msg)
    else:
        print(success_msg)
    return True