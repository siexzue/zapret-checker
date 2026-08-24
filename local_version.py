# local_version.py
import json
import os
import re

VERSION_FILE = "zapret_version.txt"


def _get_app_dir():
    import sys
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _version_file_path():
    return os.path.join(_get_app_dir(), VERSION_FILE)


def _log(message, log_callback=None):
    if log_callback:
        log_callback(message)
    else:
        print(message)


def get_local_version(zapret_path, gui_mode=False, log_callback=None):
    """Определяет установленную версию Zapret."""
    if not zapret_path or not os.path.exists(zapret_path):
        return None

    version = get_version_from_service_bat(zapret_path)
    if version:
        _log(f"🔍 Найдена версия в service.bat: {version}", log_callback)
        save_version(version)
        return version

    version = search_version_in_folder(zapret_path)
    if version:
        _log(f"🔍 Найдена версия в текстовых файлах: {version}", log_callback)
        save_version(version)
        return version

    version_file = _version_file_path()
    if os.path.exists(version_file):
        with open(version_file, 'r', encoding='utf-8') as file:
            version = file.read().strip()
            if version:
                _log(f"📝 Использую сохранённую версию: {version}", log_callback)
                return version

    if not gui_mode:
        _log(
            f"❓ Не удалось автоматически определить версию в: {zapret_path}",
            log_callback,
        )
        manual_version = input("Введите версию вручную (например, 1.9.7): ").strip()
        if manual_version:
            save_version(manual_version)
            return manual_version

    return None


def get_version_from_service_bat(zapret_path):
    """Извлекает версию из service.bat."""
    service_bat = os.path.join(zapret_path, "service.bat")
    if not os.path.exists(service_bat):
        return None

    try:
        with open(service_bat, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()

            match = re.search(
                r'set\s+"?version"?\s*=\s*"?(\d+\.\d+\.\d+[a-zA-Z]?)"?',
                content,
                re.IGNORECASE,
            )
            if match:
                return match.group(1)

            match = re.search(
                r'(?:version|ver)[:\s]+(\d+\.\d+\.\d+[a-zA-Z]?)',
                content,
                re.IGNORECASE,
            )
            if match:
                return match.group(1)

            match = re.search(r'(\d+\.\d+\.\d+[a-zA-Z]?)', content)
            if match:
                return match.group(1)
    except OSError:
        pass

    return None


def search_version_in_folder(zapret_path):
    """Ищет номер версии в .txt файлах папки Zapret."""
    if not os.path.exists(zapret_path):
        return None

    for file_name in os.listdir(zapret_path):
        if not file_name.endswith('.txt'):
            continue

        file_path = os.path.join(zapret_path, file_name)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                match = re.search(r'(\d+\.\d+\.\d+[a-zA-Z]?)', content)
                if match:
                    return match.group(1)
        except OSError:
            pass

    return None


def save_version(version, log_callback=None):
    """Сохраняет версию в файл рядом с программой."""
    with open(_version_file_path(), 'w', encoding='utf-8') as file:
        file.write(version)
    _log(f"💾 Версия {version} сохранена", log_callback)


def update_version(new_version):
    """Обновляет сохранённую версию после обновления Zapret."""
    save_version(new_version)


def clear_saved_version():
    """Удаляет сохранённую версию (при смене папки Zapret)."""
    version_file = _version_file_path()
    if os.path.exists(version_file):
        os.remove(version_file)
