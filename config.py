# config.py
import json
import os

# Версия приложения
APP_VERSION = "1.0.4"

# Репозиторий Zapret
ZAPRET_REPO = "Flowseal/zapret-discord-youtube"

# Репозиторий программы-обновлятора
APP_REPO = "siexzue/zapret-checker"

# Путь по умолчанию (можно переопределить в settings.json)
ZAPRET_PATH = ""

# Папка для временных загрузок
DOWNLOAD_FOLDER = "downloads"

# Имя архива
ARCHIVE_NAME = "zapret-discord-youtube.zip"

SETTINGS_FILE = "settings.json"


def _get_app_dir():
    import sys
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def load_settings():
    """Загружает настройки из settings.json."""
    settings_path = os.path.join(_get_app_dir(), SETTINGS_FILE)
    if os.path.exists(settings_path):
        with open(settings_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {"zapret_path": ZAPRET_PATH}


def save_settings(settings):
    """Сохраняет настройки в settings.json."""
    settings_path = os.path.join(_get_app_dir(), SETTINGS_FILE)
    with open(settings_path, 'w', encoding='utf-8') as file:
        json.dump(settings, file, indent=4, ensure_ascii=False)


def get_zapret_path():
    """Возвращает путь к Zapret из настроек или config."""
    settings = load_settings()
    return settings.get("zapret_path") or ZAPRET_PATH
