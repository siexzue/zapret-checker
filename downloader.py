# downloader.py
import os
import shutil
import zipfile

import requests

from config import DOWNLOAD_FOLDER


def _get_app_dir():
    import sys
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def download_file(url, save_path, log_callback=None):
    """Скачивает файл по URL с проверкой ответа."""
    msg = f"📥 Скачиваю: {url}"
    if log_callback:
        log_callback(msg)
    else:
        print(msg)

    response = requests.get(url, stream=True, timeout=120)
    response.raise_for_status()
    total_size = int(response.headers.get('content-length', 0))

    with open(save_path, 'wb') as file:
        downloaded = 0
        for chunk in response.iter_content(chunk_size=8192):
            if not chunk:
                continue
            file.write(chunk)
            downloaded += len(chunk)
            if total_size > 0 and not log_callback:
                percent = (downloaded / total_size) * 100
                print(f"\rПрогресс: {percent:.1f}%", end='')

    done_msg = "✅ Скачивание завершено!"
    if log_callback:
        log_callback(done_msg)
    else:
        print(f"\n{done_msg}")


def extract_zip(zip_path, extract_to, log_callback=None):
    """
    Распаковывает ZIP, извлекая содержимое без корневой подпапки архива.
    """
    msg = f"📦 Распаковываю в: {extract_to}"
    if log_callback:
        log_callback(msg)
    else:
        print(msg)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        all_files = zip_ref.namelist()
        if not all_files:
            raise ValueError("Архив пуст")

        root_folder = all_files[0].split('/')[0]

        for file_name in all_files:
            if '.github' in file_name:
                continue

            if file_name.startswith(root_folder + '/'):
                target_path = file_name[len(root_folder) + 1:]
            else:
                target_path = file_name

            if not target_path or file_name.endswith('/'):
                continue

            full_path = os.path.join(extract_to, target_path)
            parent_dir = os.path.dirname(full_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)

            with zip_ref.open(file_name) as source, open(full_path, 'wb') as target:
                target.write(source.read())

    done_msg = "✅ Распаковка завершена!"
    if log_callback:
        log_callback(done_msg)
    else:
        print(done_msg)


def update_zapret(
    zapret_path,
    download_url,
    archive_name,
    skip_confirm=False,
    log_callback=None,
):
    """Скачивает и устанавливает новую версию Zapret."""
    download_dir = os.path.join(_get_app_dir(), DOWNLOAD_FOLDER)
    os.makedirs(download_dir, exist_ok=True)
    zip_path = os.path.join(download_dir, archive_name)

    try:
        download_file(download_url, zip_path, log_callback)
    except requests.RequestException as error:
        error_msg = f"❌ Ошибка скачивания: {error}"
        if log_callback:
            log_callback(error_msg)
        else:
            print(error_msg)
        return False

    if not skip_confirm:
        print(f"\n⚠️ ВНИМАНИЕ! Будет удалена папка: {zapret_path}")
        confirm = input("Продолжить? (y/n): ").strip().lower()
        if confirm != 'y':
            msg = "❌ Отмена."
            if log_callback:
                log_callback(msg)
            else:
                print(msg)
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
                "   1. Закройте Zapret\n"
                f"   2. Удалите папку вручную: {zapret_path}\n"
                "   3. Запустите программу ещё раз\n"
                "=" * 50
            )
            if log_callback:
                log_callback(error_msg)
            else:
                print(error_msg)
            return False
        except OSError as error:
            error_msg = f"❌ Ошибка при удалении: {error}"
            if log_callback:
                log_callback(error_msg)
            else:
                print(error_msg)
            return False

    os.makedirs(zapret_path, exist_ok=True)

    try:
        extract_zip(zip_path, zapret_path, log_callback)
    except (OSError, zipfile.BadZipFile, ValueError) as error:
        error_msg = f"❌ Ошибка при распаковке: {error}"
        if log_callback:
            log_callback(error_msg)
        else:
            print(error_msg)
        return False
    finally:
        if os.path.exists(zip_path):
            try:
                os.remove(zip_path)
            except OSError:
                pass

    success_msg = "✅ Обновление завершено!"
    if log_callback:
        log_callback(success_msg)
    else:
        print(success_msg)
    return True
