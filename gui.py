# gui.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import sys
import os
import json

# Добавляем путь к модулям
sys.path.append(os.path.dirname(__file__))

from config import GITHUB_REPO, ARCHIVE_NAME
from github_api import get_latest_release
from local_version import get_local_version, update_version, save_version
from downloader import update_zapret

SETTINGS_FILE = "settings.json"

def load_settings():
    """Загружает сохранённые настройки."""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"zapret_path": ""}

def save_settings(settings):
    """Сохраняет настройки в файл."""
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=4)

class ZapretUpdaterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Zapret Auto Updater")
        self.root.geometry("650x550")
        self.root.resizable(True, True)
        
        icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)

        # Загружаем настройки
        self.settings = load_settings()
        self.zapret_path = self.settings.get("zapret_path", "")
        
        # Заголовок
        title = tk.Label(root, text="🚀 Zapret Auto Updater", 
                        font=("Arial", 16, "bold"))
        title.pack(pady=10)
        
        # === НАСТРОЙКИ ПУТИ ===
        path_frame = tk.LabelFrame(root, text="Настройки", padx=10, pady=10)
        path_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(path_frame, text="📁 Папка с Zapret:", font=("Arial", 10)).grid(row=0, column=0, sticky="w")
        
        self.path_var = tk.StringVar(value=self.zapret_path)
        self.path_entry = tk.Entry(path_frame, textvariable=self.path_var, width=50, state="readonly")
        self.path_entry.grid(row=1, column=0, padx=(0, 5), sticky="we")
        
        self.browse_btn = tk.Button(path_frame, text="📂 Обзор", command=self.browse_folder)
        self.browse_btn.grid(row=1, column=1)
        
        path_frame.columnconfigure(0, weight=1)
        
        # Инфо-панель
        self.info_frame = tk.LabelFrame(root, text="Информация", padx=10, pady=10)
        self.info_frame.pack(fill="x", padx=10, pady=5)
        
        self.version_label = tk.Label(self.info_frame, text="", font=("Arial", 10))
        self.version_label.pack(anchor="w")
        
        self.path_label = tk.Label(self.info_frame, text="", font=("Arial", 10))
        self.path_label.pack(anchor="w")
        
        self.latest_label = tk.Label(self.info_frame, text="", font=("Arial", 10))
        self.latest_label.pack(anchor="w")
        
        # Кнопки
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)
        
        self.check_btn = tk.Button(btn_frame, text="🔍 Проверить обновления", 
                                   command=self.check_updates,
                                   font=("Arial", 12), bg="#4CAF50", fg="white",
                                   padx=20, pady=10)
        self.check_btn.pack(side="left", padx=5)
        
        self.update_btn = tk.Button(btn_frame, text="⬇️ Обновить Zapret", 
                                    command=self.do_update,
                                    font=("Arial", 12), bg="#2196F3", fg="white",
                                    padx=20, pady=10, state="disabled")
        self.update_btn.pack(side="left", padx=5)
        
        # Лог
        self.log_frame = tk.LabelFrame(root, text="Лог", padx=10, pady=10)
        self.log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(self.log_frame, height=12, 
                                                   font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True)
        
        # Прогресс-бар
        self.progress = ttk.Progressbar(root, mode='indeterminate')
        self.progress.pack(fill="x", padx=10, pady=5)
        
        # Статус-бар
        self.status_label = tk.Label(root, text="Готов к работе", 
                                     font=("Arial", 9), fg="gray", anchor="w")
        self.status_label.pack(fill="x", padx=10, pady=5)
        
        # Обновляем информацию при старте
        self.update_path_display()
        self.refresh_local_version()
        
    def browse_folder(self):
        """Открывает диалог выбора папки."""
        folder = filedialog.askdirectory(title="Выберите папку с Zapret")
        if folder:
            self.zapret_path = folder
            self.path_var.set(folder)
            
            # Сохраняем настройки
            self.settings["zapret_path"] = folder
            save_settings(self.settings)
            
            # Сбрасываем сохранённую версию
            version_file = "zapret_version.txt"
            if os.path.exists(version_file):
                os.remove(version_file)
                self.log("🔄 Сброшена сохранённая версия")
            
            self.update_path_display()
            self.refresh_local_version()
            self.log(f"📁 Выбрана папка: {folder}")
            
    def update_path_display(self):
        """Обновляет отображение пути."""
        if self.zapret_path:
            self.path_label.config(text=f"📁 Путь: {self.zapret_path}")
        else:
            self.path_label.config(text="⚠️ Путь не выбран! Нажмите 'Обзор'", fg="orange")
            
    def refresh_local_version(self):
        """Обновляет информацию о локальной версии."""
        if self.zapret_path:
            self.local_version = get_local_version(self.zapret_path, gui_mode=True)  # ← добавил gui_mode=True
            if self.local_version:
                self.version_label.config(text=f"📂 Установленная версия: {self.local_version}")
            else:
                self.version_label.config(text="⚠️ Версия не определена", fg="orange")
        else:
            self.local_version = None
            self.version_label.config(text="⚠️ Выберите папку с Zapret", fg="orange")
            
    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def set_status(self, text, color="gray"):
        self.status_label.config(text=text, fg=color)
        self.root.update()
        
    def check_updates(self):
        if not self.zapret_path:
            messagebox.showwarning("Внимание", "Сначала выберите папку с Zapret!")
            return
            
        self.check_btn.config(state="disabled", text="⏳ Проверяю...")
        self.progress.start()
        self.log("=" * 50)
        self.log("🔍 Проверка обновлений...")
        self.set_status("Проверка обновлений...", "blue")
        
        thread = threading.Thread(target=self._check_updates_thread)
        thread.daemon = True
        thread.start()
        
    def _check_updates_thread(self):
        try:
            self.latest_release = get_latest_release(GITHUB_REPO)
            
            if self.latest_release:
                latest_ver = self.latest_release['version']
                self.latest_label.config(text=f"🌐 Последняя версия: {latest_ver}")
                self.log(f"✅ Последняя версия на GitHub: {latest_ver}")
                
                if self.local_version and latest_ver != self.local_version:
                    self.log(f"🔥 ДОСТУПНО ОБНОВЛЕНИЕ! ({self.local_version} → {latest_ver})")
                    self.version_label.config(
                        text=f"📂 Установленная версия: {self.local_version} → {latest_ver}",
                        fg="green"
                    )
                    self.root.after(0, lambda: self.update_btn.config(state="normal"))
                    self.set_status("Доступно обновление!", "green")
                else:
                    self.log("✅ У вас актуальная версия.")
                    self.set_status("Актуальная версия", "green")
            else:
                self.log("❌ Не удалось получить информацию о релизе.")
                self.set_status("Ошибка проверки", "red")
                
        except Exception as e:
            self.log(f"❌ Ошибка: {e}")
            self.set_status("Ошибка", "red")
        finally:
            self.root.after(0, lambda: self.check_btn.config(state="normal", text="🔍 Проверить обновления"))
            self.root.after(0, lambda: self.progress.stop())
            
    def do_update(self):
        if not self.zapret_path:
            messagebox.showwarning("Внимание", "Сначала выберите папку с Zapret!")
            return
            
        if not self.latest_release:
            messagebox.showerror("Ошибка", "Сначала проверьте обновления!")
            return
            
        answer = messagebox.askyesno(
            "Подтверждение",
            f"Будет удалена папка:\n{self.zapret_path}\n\nПродолжить?"
        )
        
        if not answer:
            return
            
        self.update_btn.config(state="disabled", text="⏳ Обновляю...")
        self.check_btn.config(state="disabled")
        self.progress.start()
        self.log("📥 Начинаю обновление...")
        self.set_status("Обновление...", "blue")
        
        thread = threading.Thread(target=self._do_update_thread)
        thread.daemon = True
        thread.start()
        
    def _do_update_thread(self):
        try:
            success = update_zapret(
                zapret_path=self.zapret_path,
                download_url=self.latest_release['download_url'],
                archive_name=ARCHIVE_NAME,
                skip_confirm=True,
                log_callback=self.log  # ← просто передаём self.log
            )
            
            if success:
                update_version(self.latest_release['version'])
                self.refresh_local_version()
                self.root.after(0, lambda: self.latest_label.config(text=""))
                self.root.after(0, lambda: self.version_label.config(fg="black"))
                self.log(f"🎉 Zapret успешно обновлён до версии {self.latest_release['version']}!")
                self.set_status("Обновление завершено!", "green")
                self.root.after(0, lambda: messagebox.showinfo("Успех", f"Zapret обновлён до версии {self.latest_release['version']}!"))
            else:
                self.log("❌ Обновление не удалось.")
                self.set_status("Ошибка обновления", "red")
                
        except Exception as e:
            self.log(f"❌ Ошибка: {e}")
            self.set_status("Ошибка", "red")
        finally:
            self.root.after(0, lambda: self.update_btn.config(state="disabled", text="⬇️ Обновить Zapret"))
            self.root.after(0, lambda: self.check_btn.config(state="normal", text="🔍 Проверить обновления"))
            self.root.after(0, lambda: self.progress.stop())

def main():
    root = tk.Tk()
    app = ZapretUpdaterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()