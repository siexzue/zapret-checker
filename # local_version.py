# local_version.py
import os
import re
import json

VERSION_FILE = "zapret_version.txt"  # Храним рядом с программой

def get_local_version(zapret_path):
    """
    Определяет версию Zapret.
    1. Сначала ищет наш собственный файл zapret_version.txt
    2. Если его нет — пытается найти в readme.txt
    3. Если нигде нет — возвращает None
    """
    
    # Вариант 1: Наш собственный файл (самый надёжный)
    our_version_file = os.path.join(os.path.dirname(__file__), VERSION_FILE)
    if os.path.exists(our_version_file):
        with open(our_version_file, 'r', encoding='utf-8') as f:
            version = f.read().strip()
            if version:
                print(f"📝 Найдена сохранённая версия: {version}")
                return version
    
    # Вариант 2: Ищем в файлах внутри папки Zapret
    version = search_version_in_folder(zapret_path)
    if version:
        # Сохраняем найденную версию в наш файл
        save_version(version)
        return version
    
    # Вариант 3: Спрашиваем у пользователя
    print(f"❓ Не удалось автоматически определить версию Zapret в папке: {zapret_path}")
    manual_version = input("Введите версию вручную (например, 1.9.7): ").strip()
    if manual_version:
        save_version(manual_version)
        return manual_version
    
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
                    # Ищем паттерн типа 1.9.7 или 1.9.7b
                    match = re.search(r'(\d+\.\d+\.\d+[a-z]?)', content)
                    if match:
                        version = match.group(1)
                        print(f"🔍 Найдена версия {version} в файле {file}")
                        return version
            except:
                pass
    return None

def save_version(version):
    """Сохраняет версию в файл рядом с программой."""
    our_version_file = os.path.join(os.path.dirname(__file__), VERSION_FILE)
    with open(our_version_file, 'w', encoding='utf-8') as f:
        f.write(version)
    print(f"💾 Версия {version} сохранена в {VERSION_FILE}")

def update_version(new_version):
    """Обновляет сохранённую версию после обновления Zapret."""
    save_version(new_version)