# app_updater.py
"""Модуль для автообновления самой программы ZapretUpdater."""
import os
import sys
import requests
import json
import re
import subprocess
import tempfile


def get_app_version():
    """Получает текущую версию приложения из config.py."""
    try:
        from config import APP_VERSION
        return APP_VERSION
    except ImportError:
        return "0.0.0"


def get_latest_app_version(repo):
    """Получает последнюю версию приложения с GitHub."""
    # Импортируем из github_api
    try:
        from github_api import get_latest_app_release
        return get_latest_app_release(repo)
    except ImportError:
        return None


def compare_versions(v1, v2):
    """
    Сравнивает две версии.
    Возвращает:
      -1 если v1 < v2 (нужно обновление)
       0 если v1 == v2
       1 если v1 > v2
    """
    def normalize(v):
        # Убираем буквы и разбиваем на части
        v = re.sub(r'[a-zA-Z]', '', v)
        return [int(x) for x in v.split('.')]

    try:
        parts1 = normalize(v1)
        parts2 = normalize(v2)

        # Дополняем до одинаковой длины
        max_len = max(len(parts1), len(parts2))
        parts1.extend([0] * (max_len - len(parts1)))
        parts2.extend([0] * (max_len - len(parts2)))

        if parts1 < parts2:
            return -1
        elif parts1 > parts2:
            return 1
        else:
            return 0
    except:
        return 0


def check_for_app_updates(repo):
    """Проверяет наличие обновлений приложения."""
    current_version = get_app_version()
    latest = get_latest_app_version(repo)

    if not latest:
        return None

    comparison = compare_versions(current_version, latest['version'])

    if comparison < 0:
        # Доступно обновление
        return {
            "current": current_version,
            "latest": latest['version'],
            "download_url": latest['download_url'],
            "html_url": latest['html_url']
        }

    return None


def download_update(download_url, progress_callback=None):
    """Скачивает обновление приложения."""
    try:
        if progress_callback:
            progress_callback("📥 Скачиваю обновление...")

        response = requests.get(download_url, stream=True, timeout=60)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))

        # Сохраняем во временную папку
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, "ZapretUpdater_new.exe")

        with open(temp_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0 and progress_callback:
                    percent = int((downloaded / total_size) * 100)
                    progress_callback(f"⏳ Загрузка: {percent}%")

        if progress_callback:
            progress_callback("✅ Скачивание завершено!")

        return temp_path

    except Exception as e:
        if progress_callback:
            progress_callback(f"❌ Ошибка загрузки: {e}")
        return None


def install_update(new_exe_path, html_url):
    """
    Устанавливает обновление.
    Если запущено из .exe — заменяет файл и перезапускает.
    Если запущено из Python — скачивает .exe рядом и запускает его.
    """
    try:
        if getattr(sys, 'frozen', False):
            # Скомпилированная версия — заменяем .exe
            current_exe = sys.executable

            # Создаем batch-файл для замены
            temp_dir = tempfile.gettempdir()
            batch_path = os.path.join(temp_dir, "update_app.bat")

            batch_content = f'''@echo off
timeout /t 2 /nobreak >nul
echo Заменяю файл...
copy /y "{new_exe_path}" "{current_exe}" >nul
if %errorlevel%==0 (
    echo ✅ Обновление установлено!
    echo Запускаю обновленную версию...
    start "" "{current_exe}"
) else (
    echo ❌ Ошибка при замене файла
    pause
)
del "%~f0"
'''

            with open(batch_path, 'w', encoding='utf-8') as f:
                f.write(batch_content)

            # Запускаем batch-файл скрыто
            subprocess.Popen(
                batch_path,
                creationflags=subprocess.CREATE_NO_WINDOW,
                shell=True
            )

            # Закрываем текущее приложение
            os._exit(0)
            return True
        else:
            # Python режим — копируем .exe рядом с программой и запускаем
            app_dir = os.path.dirname(os.path.abspath(__file__))
            new_app_name = "ZapretChecker_new.exe"
            dest_path = os.path.join(app_dir, new_app_name)

            # Копируем скачанный файл
            import shutil
            shutil.copy2(new_exe_path, dest_path)

            # Запускаем новый .exe
            subprocess.Popen(
                f'"{dest_path}"',
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                shell=True
            )

            # Закрываем Python версию
            print(f"✅ Новая версия запущена: {dest_path}")
            print(f"💡 Закройте эту консоль и используйте новый .exe")
            sys.exit(0)
            return True

    except Exception as e:
        print(f"❌ Ошибка установки обновления: {e}")
        return False
