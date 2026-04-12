# gui.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import sys
import os
import json

sys.path.append(os.path.dirname(__file__))

from config import GITHUB_REPO, ARCHIVE_NAME
from github_api import get_latest_release
from local_version import get_local_version, update_version
from downloader import update_zapret

SETTINGS_FILE = "settings.json"
ICON_FILE = "icon.ico"

# 🎨 МИНИМАЛИСТИЧНАЯ ЦВЕТОВАЯ СХЕМА
COLORS = {
    "bg": "#1a1a1a",           # Тёмный фон
    "fg": "#ffffff",           # Белый текст
    "accent": "#6c5ce7",       # Фиолетовый акцент
    "success": "#00b894",      # Зелёный
    "error": "#d63031",        # Красный
    "warning": "#fdcb6e",      # Жёлтый
    "card": "#2d2d2d",         # Цвет карточек
    "entry": "#3d3d3d",        # Цвет полей ввода
    "log": "#1e1e1e",          # Цвет лога
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"zapret_path": ""}

def save_settings(settings):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=4)

class ModernButton(tk.Button):
    """Стильная кнопка с эффектом наведения."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.config(
            relief=tk.FLAT,
            borderwidth=0,
            font=("Segoe UI", 11, "bold"),
            padx=20,
            pady=10,
            cursor="hand2"
        )

class ZapretUpdaterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Zapret Updater")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        self.root.configure(bg=COLORS["bg"])
        
        # Иконка
        try:
            icon_path = os.path.join(os.path.dirname(__file__), ICON_FILE)
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
            elif getattr(sys, 'frozen', False):
                self.root.iconbitmap(sys.executable)
        except:
            pass
        
        self.settings = load_settings()
        self.zapret_path = self.settings.get("zapret_path", "")
        self.local_version = None
        self.latest_release = None
        
        self.setup_ui()
        self.refresh_local_version()
        
    def setup_ui(self):
        # Главный контейнер
        main_frame = tk.Frame(self.root, bg=COLORS["bg"])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Заголовок
        title = tk.Label(
            main_frame,
            text="⚡ Zapret Updater",
            font=("Segoe UI", 20, "bold"),
            fg=COLORS["accent"],
            bg=COLORS["bg"]
        )
        title.pack(pady=(0, 20))
        
        # Карточка с путём
        path_card = tk.Frame(main_frame, bg=COLORS["card"], bd=0)
        path_card.pack(fill="x", pady=(0, 15))
        
        tk.Label(
            path_card,
            text="📁 Путь к Zapret",
            font=("Segoe UI", 10),
            fg=COLORS["fg"],
            bg=COLORS["card"]
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        path_row = tk.Frame(path_card, bg=COLORS["card"])
        path_row.pack(fill="x", padx=15, pady=(0, 15))
        
        self.path_var = tk.StringVar(value=self.zapret_path if self.zapret_path else "Не выбран")
        self.path_entry = tk.Entry(
            path_row,
            textvariable=self.path_var,
            font=("Segoe UI", 9),
            bg=COLORS["entry"],
            fg=COLORS["fg"],
            relief=tk.FLAT,
            state="readonly",
            readonlybackground=COLORS["entry"]
        )
        self.path_entry.pack(side="left", fill="x", expand=True)
        
        ModernButton(
            path_row,
            text="Обзор",
            command=self.browse_folder,
            bg=COLORS["accent"],
            fg="white"
        ).pack(side="left", padx=(10, 0))
        
        # Карточка с информацией
        info_card = tk.Frame(main_frame, bg=COLORS["card"], bd=0)
        info_card.pack(fill="x", pady=(0, 15))
        
        self.version_label = tk.Label(
            info_card,
            text="Версия: не определена",
            font=("Segoe UI", 11),
            fg=COLORS["fg"],
            bg=COLORS["card"]
        )
        self.version_label.pack(anchor="w", padx=15, pady=15)
        
        # Кнопки
        btn_frame = tk.Frame(main_frame, bg=COLORS["bg"])
        btn_frame.pack(fill="x", pady=(0, 15))
        
        self.check_btn = ModernButton(
            btn_frame,
            text="🔍 Проверить обновления",
            command=self.check_updates,
            bg=COLORS["accent"],
            fg="white"
        )
        self.check_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.update_btn = ModernButton(
            btn_frame,
            text="⬇️ Обновить",
            command=self.do_update,
            bg=COLORS["card"],
            fg=COLORS["fg"],
            state="disabled"
        )
        self.update_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        # Лог
        log_frame = tk.Frame(main_frame, bg=COLORS["log"], bd=0)
        log_frame.pack(fill="both", expand=True)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=8,
            font=("Consolas", 9),
            bg=COLORS["log"],
            fg="#a0a0a0",
            relief=tk.FLAT,
            borderwidth=0
        )
        self.log_text.pack(fill="both", expand=True, padx=1, pady=1)
        
        # Прогресс-бар (скрытый)
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        
        # Статус
        self.status_label = tk.Label(
            main_frame,
            text="● Готов",
            font=("Segoe UI", 9),
            fg=COLORS["success"],
            bg=COLORS["bg"],
            anchor="w"
        )
        self.status_label.pack(fill="x", pady=(10, 0))
        
    def browse_folder(self):
        folder = filedialog.askdirectory(title="Выберите папку с Zapret")
        if folder:
            self.zapret_path = folder
            self.path_var.set(folder)
            self.settings["zapret_path"] = folder
            save_settings(self.settings)
            
            version_file = "zapret_version.txt"
            if os.path.exists(version_file):
                os.remove(version_file)
            
            self.refresh_local_version()
            self.log(f"📁 {folder}")
            
    def refresh_local_version(self):
        if self.zapret_path:
            self.local_version = get_local_version(self.zapret_path, gui_mode=True)
            if self.local_version:
                self.version_label.config(text=f"📦 {self.local_version}")
            else:
                self.version_label.config(text="⚠️ Версия не найдена")
        else:
            self.local_version = None
            self.version_label.config(text="📂 Выберите папку")
            
    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def set_status(self, text, color=None):
        if color is None:
            color = COLORS["success"]
        self.status_label.config(text=f"● {text}", fg=color)
        self.root.update()
        
    def check_updates(self):
        if not self.zapret_path:
            messagebox.showwarning("Внимание", "Выберите папку с Zapret")
            return
            
        self.check_btn.config(state="disabled", text="⏳ Проверка...")
        self.progress.pack(fill="x", pady=(0, 10))
        self.progress.start()
        self.set_status("Проверка обновлений...", COLORS["warning"])
        
        thread = threading.Thread(target=self._check_updates_thread)
        thread.daemon = True
        thread.start()
        
    def _check_updates_thread(self):
        try:
            self.latest_release = get_latest_release(GITHUB_REPO)
            
            if self.latest_release:
                latest_ver = self.latest_release['version']
                self.log(f"✓ Последняя версия: {latest_ver}")
                
                if self.local_version and latest_ver != self.local_version:
                    self.log(f"🔥 Доступно обновление! ({self.local_version} → {latest_ver})")
                    self.version_label.config(text=f"📦 {self.local_version} → {latest_ver}", fg=COLORS["warning"])
                    self.root.after(0, lambda: self.update_btn.config(
                        state="normal", bg=COLORS["success"], fg="white"
                    ))
                    self.root.after(0, lambda: self.set_status("Доступно обновление", COLORS["warning"]))
                else:
                    self.log("✓ Актуальная версия")
                    self.root.after(0, lambda: self.set_status("Актуальная версия", COLORS["success"]))
            else:
                self.log("✗ Ошибка получения релиза")
                self.root.after(0, lambda: self.set_status("Ошибка", COLORS["error"]))
                
        except Exception as e:
            self.log(f"✗ Ошибка: {e}")
            self.root.after(0, lambda: self.set_status("Ошибка", COLORS["error"]))
        finally:
            self.root.after(0, lambda: self.check_btn.config(state="normal", text="🔍 Проверить обновления"))
            self.root.after(0, lambda: self.progress.stop())
            self.root.after(0, lambda: self.progress.pack_forget())
            
    def do_update(self):
        if not self.latest_release:
            return
            
        answer = messagebox.askyesno(
            "Подтверждение",
            f"Удалить папку:\n{self.zapret_path}\n\nи установить новую версию?"
        )
        
        if not answer:
            return
            
        self.update_btn.config(state="disabled", text="⏳ Обновление...")
        self.check_btn.config(state="disabled")
        self.progress.pack(fill="x", pady=(0, 10))
        self.progress.start()
        self.set_status("Обновление...", COLORS["warning"])
        
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
                log_callback=self.log
            )
            
            if success:
                update_version(self.latest_release['version'])
                self.refresh_local_version()
                self.log(f"🎉 Успешно обновлено до {self.latest_release['version']}")
                self.root.after(0, lambda: self.set_status("Обновлено!", COLORS["success"]))
                self.root.after(0, lambda: messagebox.showinfo("Успех", "Zapret обновлён!"))
            else:
                self.log("✗ Ошибка обновления")
                self.root.after(0, lambda: self.set_status("Ошибка", COLORS["error"]))
                
        except Exception as e:
            self.log(f"✗ Ошибка: {e}")
            self.root.after(0, lambda: self.set_status("Ошибка", COLORS["error"]))
        finally:
            self.root.after(0, lambda: self.update_btn.config(
                state="disabled", text="⬇️ Обновить", bg=COLORS["card"], fg=COLORS["fg"]
            ))
            self.root.after(0, lambda: self.check_btn.config(state="normal", text="🔍 Проверить обновления"))
            self.root.after(0, lambda: self.progress.stop())
            self.root.after(0, lambda: self.progress.pack_forget())

def main():
    root = tk.Tk()
    app = ZapretUpdaterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()