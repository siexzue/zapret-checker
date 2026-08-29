# gui.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import sys
import os

sys.path.append(os.path.dirname(__file__))

from config import ZAPRET_REPO, ARCHIVE_NAME, APP_REPO, load_settings, save_settings
from github_api import get_latest_release
from local_version import get_local_version, update_version, clear_saved_version
from downloader import update_zapret
from app_updater import check_for_app_updates, download_update, install_update
from version_utils import is_update_available, normalize_version
ICON_FILE = "icon.ico"

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
        self.root.title("Zapret Updater v1.0")
        self.root.geometry("600x500")
        self.root.resizable(False, False)

        # Определяем темы
        self.themes = {
            "dark": {
                "bg": "#1a1a1a",
                "fg": "#ffffff",
                "accent": "#6c5ce7",
                "success": "#00b894",
                "error": "#d63031",
                "warning": "#fdcb6e",
                "card": "#2d2d2d",
                "entry": "#3d3d3d",
                "log": "#1e1e1e",
            },
            "light": {
                "bg": "#f0f0f0",
                "fg": "#000000",
                "accent": "#3b82f6",
                "success": "#22c55e",
                "error": "#ef4444",
                "warning": "#f59e0b",
                "card": "#ffffff",
                "entry": "#e5e7eb",
                "log": "#f9fafb",
            }
        }

        # Загружаем настройки и выбираем тему
        self.settings = load_settings()
        self.current_theme = self.settings.get("theme", "dark")
        if self.current_theme not in self.themes:
            self.current_theme = "dark"
        self.colors = self.themes[self.current_theme].copy()
        self.root.configure(bg=self.colors["bg"])

        # Иконка
        try:
            icon_path = os.path.join(os.path.dirname(__file__), ICON_FILE)
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
            elif getattr(sys, 'frozen', False):
                self.root.iconbitmap(sys.executable)
        except:
            pass

        self.zapret_path = self.settings.get("zapret_path", "")
        self.local_version = None
        self.latest_release = None

        self.setup_ui()
        self.apply_theme()  # применяем цвета при старте
        self.refresh_local_version()

        if self.zapret_path:
            self.root.after(1500, self.check_updates)

        if getattr(sys, 'frozen', False):
            self.root.after(1000, self.check_app_updates)

    def setup_ui(self):
        # Главный контейнер
        self.main_frame = tk.Frame(self.root, bg=self.colors["bg"])
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Кнопка переключения темы (внутри main_frame)
        theme_label = "🌙 Тёмная" if self.current_theme == "dark" else "☀️ Светлая"
        self.theme_btn = ModernButton(
            self.main_frame,
            text=theme_label,
            command=self.toggle_theme,
            bg=self.colors["card"],
            fg=self.colors["accent"]
        )
        self.theme_btn.pack(pady=(0, 10))

        # Заголовок
        self.title_label = tk.Label(
            self.main_frame,
            text="⚡ Zapret Updater",
            font=("Segoe UI", 20, "bold"),
            fg=self.colors["accent"],
            bg=self.colors["bg"]
        )
        self.title_label.pack(pady=(0, 20))

        # Карточка с путём
        self.path_card = tk.Frame(self.main_frame, bg=self.colors["card"], bd=0)
        self.path_card.pack(fill="x", pady=(0, 15))

        tk.Label(
            self.path_card,
            text="📁 Путь к Zapret",
            font=("Segoe UI", 10),
            fg=self.colors["fg"],
            bg=self.colors["card"]
        ).pack(anchor="w", padx=15, pady=(15, 5))

        path_row = tk.Frame(self.path_card, bg=self.colors["card"])
        path_row.pack(fill="x", padx=15, pady=(0, 15))

        self.path_var = tk.StringVar(value=self.zapret_path if self.zapret_path else "Не выбран")
        self.path_entry = tk.Entry(
            path_row,
            textvariable=self.path_var,
            font=("Segoe UI", 9),
            bg=self.colors["entry"],
            fg=self.colors["fg"],
            relief=tk.FLAT,
            state="readonly",
            readonlybackground=self.colors["entry"]
        )
        self.path_entry.pack(side="left", fill="x", expand=True)

        self.browse_btn = ModernButton(
            path_row,
            text="Обзор",
            command=self.browse_folder,
            bg=self.colors["accent"],
            fg="white"
        )
        self.browse_btn.pack(side="left", padx=(10, 0))

        # Карточка с информацией
        self.info_card = tk.Frame(self.main_frame, bg=self.colors["card"], bd=0)
        self.info_card.pack(fill="x", pady=(0, 15))

        self.version_label = tk.Label(
            self.info_card,
            text="Версия: не определена",
            font=("Segoe UI", 11),
            fg=self.colors["fg"],
            bg=self.colors["card"]
        )
        self.version_label.pack(anchor="w", padx=15, pady=15)

        # Кнопки действий
        btn_frame = tk.Frame(self.main_frame, bg=self.colors["bg"])
        btn_frame.pack(fill="x", pady=(0, 15))

        self.check_btn = ModernButton(
            btn_frame,
            text="🔍 Проверить обновления",
            command=self.check_updates,
            bg=self.colors["accent"],
            fg="white"
        )
        self.check_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.update_btn = ModernButton(
            btn_frame,
            text="⬇️ Обновить",
            command=self.do_update,
            bg=self.colors["card"],
            fg=self.colors["fg"],
            state="disabled"
        )
        self.update_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # Лог
        self.log_frame = tk.Frame(self.main_frame, bg=self.colors["log"], bd=0)
        self.log_frame.pack(fill="both", expand=True)

        self.log_text = scrolledtext.ScrolledText(
            self.log_frame,
            height=8,
            font=("Consolas", 9),
            bg=self.colors["log"],
            fg=self.colors["fg"],
            relief=tk.FLAT,
            borderwidth=0
        )
        self.log_text.pack(fill="both", expand=True, padx=1, pady=1)

        # Прогресс-бар (скрытый)
        self.progress = ttk.Progressbar(self.main_frame, mode='indeterminate')

        # Статус
        self.status_label = tk.Label(
            self.main_frame,
            text="● Готов",
            font=("Segoe UI", 9),
            fg=self.colors["success"],
            bg=self.colors["bg"],
            anchor="w"
        )
        self.status_label.pack(fill="x", pady=(10, 0))

    def apply_theme(self):
        """Применяет текущую цветовую тему ко всем виджетам."""
        colors = self.colors
        self.root.configure(bg=colors["bg"])
        self.main_frame.configure(bg=colors["bg"])

        # Обновляем все дочерние виджеты рекурсивно
        def update_widgets(widget):
            if widget == self.theme_btn or widget == self.browse_btn:
                # У кнопок своя обработка
                widget.configure(bg=colors["card"], fg=colors["accent"])
            elif isinstance(widget, ModernButton):
                # Обычные кнопки (check, update) тоже обновляем
                widget.configure(bg=colors["bg"] if widget["state"] == "disabled" else colors["accent"],
                                 fg=colors["fg"] if widget["state"] == "disabled" else "white")
            elif isinstance(widget, tk.Label):
                widget.configure(bg=colors["bg"] if widget.master == self.main_frame else colors["card"],
                                 fg=colors["fg"])
            elif isinstance(widget, tk.Frame):
                widget.configure(bg=colors["bg"] if widget.master == self.main_frame else colors["card"])
            elif isinstance(widget, tk.Entry):
                widget.configure(bg=colors["entry"], fg=colors["fg"],
                                 readonlybackground=colors["entry"])
            elif isinstance(widget, scrolledtext.ScrolledText):
                widget.configure(bg=colors["log"], fg=colors["fg"])
            elif isinstance(widget, ttk.Progressbar):
                pass  # не меняем
            else:
                try:
                    widget.configure(bg=colors["bg"], fg=colors["fg"])
                except:
                    pass

            for child in widget.winfo_children():
                update_widgets(child)

        update_widgets(self.root)
        # Особо обновляем кнопки темы и обзора (они уже обновлены через условие)
        self.theme_btn.configure(text="🌙 Тёмная" if self.current_theme == "dark" else "☀️ Светлая",
                                 bg=colors["card"], fg=colors["accent"])
        self.browse_btn.configure(bg=colors["accent"], fg="white")
        self.check_btn.configure(bg=colors["accent"], fg="white")
        if self.update_btn["state"] == "disabled":
            self.update_btn.configure(bg=colors["card"], fg=colors["fg"])
        else:
            self.update_btn.configure(bg=colors["success"], fg="white")
        self.status_label.configure(fg=colors["success"] if self.status_label["text"].startswith("● Готов") else colors["fg"])
        # Обновляем заголовок
        self.title_label.configure(fg=colors["accent"])
        # Версионная метка
        self.version_label.configure(fg=colors["fg"], bg=colors["card"])

    def toggle_theme(self):
        """Переключает тему и сохраняет выбор."""
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.colors = self.themes[self.current_theme].copy()
        self.settings["theme"] = self.current_theme
        save_settings(self.settings)
        self.apply_theme()

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Выберите папку с Zapret")
        if folder:
            self.zapret_path = folder
            self.path_var.set(folder)
            self.settings["zapret_path"] = folder
            save_settings(self.settings)

            clear_saved_version()
            self.refresh_local_version()
            self.update_btn.config(state="disabled", bg=self.colors["card"], fg=self.colors["fg"])
            self.latest_release = None
            self.log(f"📁 {folder}")

    def refresh_local_version(self):
        if self.zapret_path:
            self.local_version = get_local_version(
                self.zapret_path,
                gui_mode=True,
                log_callback=self.log,
            )
            if self.local_version:
                self.version_label.config(
                    text=f"📦 {self.local_version}",
                    fg=self.colors["fg"],
                )
            else:
                self.version_label.config(
                    text="⚠️ Версия не найдена",
                    fg=self.colors["warning"],
                )
        else:
            self.local_version = None
            self.version_label.config(
                text="📂 Выберите папку",
                fg=self.colors["fg"],
            )

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()

    def set_status(self, text, color=None):
        if color is None:
            color = self.colors["success"]
        self.status_label.config(text=f"● {text}", fg=color)
        self.root.update()

    def check_updates(self):
        if not self.zapret_path:
            messagebox.showwarning("Внимание", "Выберите папку с Zapret")
            return

        self.check_btn.config(state="disabled", text="⏳ Проверка...")
        self.progress.pack(fill="x", pady=(0, 10))
        self.progress.start()
        self.set_status("Проверка обновлений...", self.colors["warning"])

        thread = threading.Thread(target=self._check_updates_thread)
        thread.daemon = True
        thread.start()

    def _check_updates_thread(self):
        try:
            self.latest_release = get_latest_release(ZAPRET_REPO)

            if self.latest_release:
                latest_ver = self.latest_release['version']
                self.log(f"✓ Последняя версия: {latest_ver}")

                if self.local_version and is_update_available(self.local_version, latest_ver):
                    self.log(f"🔥 Доступно обновление! ({self.local_version} → {latest_ver})")
                    self.root.after(0, lambda: self.version_label.config(
                        text=f"📦 {self.local_version} → {latest_ver}",
                        fg=self.colors["warning"],
                    ))
                    self.root.after(0, lambda: self.update_btn.config(
                        state="normal", bg=self.colors["success"], fg="white"
                    ))
                    self.root.after(0, lambda: self.set_status("Доступно обновление", self.colors["warning"]))
                else:
                    self.log("✓ Актуальная версия")
                    self.root.after(0, lambda: self.version_label.config(
                        text=f"📦 {self.local_version or latest_ver}",
                        fg=self.colors["success"],
                    ))
                    self.root.after(0, lambda: self.update_btn.config(
                        state="disabled", bg=self.colors["card"], fg=self.colors["fg"]
                    ))
                    self.root.after(0, lambda: self.set_status("Актуальная версия", self.colors["success"]))
            else:
                self.log("✗ Ошибка получения релиза")
                self.root.after(0, lambda: self.set_status("Ошибка", self.colors["error"]))

        except Exception as e:
            self.log(f"✗ Ошибка: {e}")
            self.root.after(0, lambda: self.set_status("Ошибка", self.colors["error"]))
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
        self.set_status("Обновление...", self.colors["warning"])

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
                new_version = self.latest_release['version']
                update_version(new_version)
                self.local_version = new_version
                self.root.after(0, lambda: self.version_label.config(
                    text=f"📦 {new_version}",
                    fg=self.colors["success"],
                ))
                self.log(f"🎉 Успешно обновлено до {new_version}")
                self.root.after(0, lambda: self.set_status("Обновлено!", self.colors["success"]))
                self.root.after(0, lambda: messagebox.showinfo("Успех", "Zapret обновлён!"))
            else:
                self.log("✗ Ошибка обновления")
                self.root.after(0, lambda: self.set_status("Ошибка", self.colors["error"]))

        except Exception as e:
            self.log(f"✗ Ошибка: {e}")
            self.root.after(0, lambda: self.set_status("Ошибка", self.colors["error"]))
        finally:
            self.root.after(0, lambda: self.update_btn.config(
                state="disabled", text="⬇️ Обновить", bg=self.colors["card"], fg=self.colors["fg"]
            ))
            self.root.after(0, lambda: self.check_btn.config(state="normal", text="🔍 Проверить обновления"))
            self.root.after(0, lambda: self.progress.stop())
            self.root.after(0, lambda: self.progress.pack_forget())

    def check_app_updates(self):
        """Проверяет обновления самого приложения Zapret Updater."""
        update_info = check_for_app_updates(APP_REPO)

        if update_info:
            current = normalize_version(update_info['current'])
            latest = normalize_version(update_info['latest'])
            self.log(f"🔔 Updater: {current} → {latest}")

            answer = messagebox.askyesno(
                "Обновление Zapret Updater",
                f"Доступна новая версия программы-обновлятора.\n\n"
                f"Текущая: {current}\n"
                f"Новая: {latest}\n\n"
                f"Обновить Zapret Updater?\n"
                f"(Это не связано с версией самого Zapret)"
            )

            if answer:
                self._do_app_update(update_info)

    def _do_app_update(self, update_info):
        """Скачивает и устанавливает обновление приложения."""
        self.log("📥 Начинаю загрузку обновления приложения...")
        self.set_status("Обновление приложения...", self.colors["warning"])

        def progress_callback(msg):
            self.log(msg)
            self.root.update()

        new_exe = download_update(update_info['download_url'], progress_callback)

        if new_exe:
            self.log("✅ Обновление скачано, устанавливаю...")
            success = install_update(new_exe, update_info['html_url'])
            if success == True:
                self.log("🎉 Приложение будет перезапущено с новой версией!")
            else:
                self.log("❌ Ошибка при установке обновления")
                self.set_status("Ошибка обновления", self.colors["error"])
        else:
            self.log("❌ Не удалось скачать обновление")
            self.set_status("Ошибка обновления", self.colors["error"])

def main():
    root = tk.Tk()
    app = ZapretUpdaterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()