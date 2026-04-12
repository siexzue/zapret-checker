# local_version.py
import os
import re
import json

VERSION_FILE = "zapret_version.txt"

def get_local_version(zapret_path, gui_mode=False):
    """
    Определяет версию Zapret.
    """
    if not zapret_path or not os.path.exists(zapret_path):
        return None
    
    # Способ 1: Ищем в service.bat
    version = get_version_from_service_bat(zapret_path)
    if version:
        print(f"🔍 Найдена версия в service.bat: {version}")
        save_version(version)
        return version
    
    # Способ 2: Ищем в .txt файлах
    version = search_version_in_folder(zapret_path)
    if version:
        print(f"🔍 Найдена версия в текстовых файлах: {version}")
        save_version(version)
        return version
    
    # Способ 3: Сохранённая версия
    our_version_file = os.path.join(os.path.dirname(__file__), VERSION_FILE)
    if os.path.exists(our_version_file):
        with open(our_version_file, 'r', encoding='utf-8') as f:
            version = f.read().strip()
            if version:
                print(f"📝 Использую сохранённую версию: {version}")
                return version
    
    # Способ 4: Ручной ввод (только для консоли)
    if not gui_mode:
        print(f"❓ Не удалось автоматически определить версию Zapret в папке: {zapret_path}")
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
        with open(service_bat, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Ищем set version=1.9.7b
            match = re.search(r'set\s+"?version"?\s*=\s*"?(\d+\.\d+\.\d+[a-z]?)"?', content, re.IGNORECASE)
            if match:
                return match.group(1)
            
            # Ищем echo Version: 1.9.7b
            match = re.search(r'(?:version|ver)[:\s]+(\d+\.\d+\.\d+[a-z]?)', content, re.IGNORECASE)
            if match:
                return match.group(1)
            
            # Ищем просто версию в начале файла
            match = re.search(r'(\d+\.\d+\.\d+[a-z]?)', content)
            if match:
                return match.group(1)
    except:
        pass
    
    return None

def search_version_in_folder(zapret_path):
    """Ищет номер версии во всех .txt файлах папки Zapret."""
    if not os.path.exists(zapret_path):
        return None
    
    for file in os.listdir(zapret_path):
        if file.endswith('.txt'):
            file_path = os.path.join(zapret_path, file)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    match = re.search(r'(\d+\.\d+\.\d+[a-z]?)', content)
                    if match:
                        return match.group(1)
            except:
                pass
    return None

def save_version(version):
    """Сохраняет версию в файл рядом с программой."""
    our_version_file = os.path.join(os.path.dirname(__file__), VERSION_FILE)
    with open(our_version_file, 'w', encoding='utf-8') as f:
        f.write(version)
    print(f"💾 Версия {version} сохранена")

def update_version(new_version):
    """Обновляет сохранённую версию после обновления Zapret."""
    save_version(new_version)