import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import os
import threading
from pathlib import Path


class VideoSplitterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Видеорезка - нарезка видео по сегментам")
        self.root.geometry("750x600")
        self.root.resizable(True, True)
        self.root.configure(bg="#C04A4A")

        # Переменные
        self.input_file = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.segment_duration = tk.StringVar(value="60")
        self.status_text = tk.StringVar(value="Готов к работе")

        # Создаем интерфейс
        self.create_widgets()

    def create_widgets(self):
        # Основной фрейм с отступами
        main_frame = tk.Frame(self.root, bg="#C04A4A")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Внутренний белый фрейм
        self.content = tk.Frame(main_frame, bg="white", bd=0)
        self.content.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        title_label = tk.Label(self.content, text="Нарезка видео на сегменты",
                               font=('Arial', 18, 'bold'), bg="white", fg="#C04A4A")
        title_label.pack(pady=(30, 25))

        # Блок выбора входного файла
        file_frame = tk.LabelFrame(self.content, text="Исходное видео",
                                   font=('Arial', 10, 'bold'), bg="white", fg="#333", padx=10, pady=10)
        file_frame.pack(fill=tk.X, pady=(0, 15), padx=20)

        self.file_entry = tk.Entry(file_frame, textvariable=self.input_file, state='readonly',
                                   font=('Arial', 9), bg="#f5f5f5", relief="sunken", bd=1)
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        self.browse_btn = tk.Button(file_frame, text="Обзор...", command=self.select_input_file,
                                    bg="#C04A4A", fg="white", font=('Arial', 9, 'bold'),
                                    padx=15, pady=3, relief="raised", bd=1, cursor="hand2")
        self.browse_btn.pack(side=tk.RIGHT)

        # Блок выбора папки сохранения
        output_frame = tk.LabelFrame(self.content, text="Куда сохранить",
                                     font=('Arial', 10, 'bold'), bg="white", fg="#333", padx=10, pady=10)
        output_frame.pack(fill=tk.X, pady=(0, 15), padx=20)

        tk.Entry(output_frame, textvariable=self.output_dir, state='readonly',
                 font=('Arial', 9), bg="#f5f5f5", relief="sunken", bd=1).pack(side=tk.LEFT, fill=tk.X, expand=True,
                                                                              padx=(0, 10))
        tk.Button(output_frame, text="Обзор...", command=self.select_output_dir,
                  bg="#C04A4A", fg="white", font=('Arial', 9, 'bold'),
                  padx=15, pady=3, relief="raised", bd=1, cursor="hand2").pack(side=tk.RIGHT)

        # Блок настроек длительности
        duration_frame = tk.LabelFrame(self.content, text="Настройки нарезки",
                                       font=('Arial', 10, 'bold'), bg="white", fg="#333", padx=10, pady=10)
        duration_frame.pack(fill=tk.X, pady=(0, 15), padx=20)

        tk.Label(duration_frame, text="Длительность сегмента (секунд):",
                 font=('Arial', 10), bg="white", fg="#333").pack(side=tk.LEFT, padx=(0, 10))

        self.duration_spinbox = tk.Spinbox(duration_frame, from_=1, to=3600, textvariable=self.segment_duration,
                                           width=12, font=('Arial', 10), bg="white", relief="sunken", bd=1)
        self.duration_spinbox.pack(side=tk.LEFT)

        tk.Label(duration_frame, text="(от 1 до 3600 сек)",
                 font=('Arial', 9), bg="white", fg="#666").pack(side=tk.LEFT, padx=(10, 0))

        # Информация о видео
        info_frame = tk.LabelFrame(self.content, text="Информация о видео",
                                   font=('Arial', 10, 'bold'), bg="white", fg="#333", padx=10, pady=10)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20), padx=20)

        self.info_text = tk.Text(info_frame, height=6, wrap=tk.WORD,
                                 font=('Consolas', 9), bg="#f9f9f9", fg="#333",
                                 relief="sunken", bd=1, state='disabled')
        self.info_text.pack(fill=tk.BOTH, expand=True)

        # Кнопка НАРЕЗАТЬ
        button_frame = tk.Frame(self.content, bg="white")
        button_frame.pack(pady=(0, 20))

        self.process_btn = tk.Button(button_frame, text="▶ НАРЕЗАТЬ ВИДЕО",
                                     command=self.start_processing,
                                     bg="#C04A4A", fg="white",
                                     font=('Arial', 14, 'bold'),
                                     width=20, height=2,
                                     relief="raised", bd=2,
                                     cursor="hand2",
                                     activebackground="#A33A3A",
                                     activeforeground="white")
        self.process_btn.pack()

        # Прогресс-бар
        self.progress = ttk.Progressbar(self.content, mode='indeterminate', length=400)
        self.progress.pack(pady=(0, 10))

        # Статус
        self.status_label = tk.Label(self.content, textvariable=self.status_text,
                                     font=('Arial', 9), bg="white", fg="#666")
        self.status_label.pack(pady=(0, 20))

    def select_input_file(self):
        file_path = filedialog.askopenfilename(
            title="Выберите видеофайл",
            filetypes=[("Видео файлы", "*.mp4 *.avi *.mkv *.mov *.flv *.wmv"),
                       ("Все файлы", "*.*")]
        )
        if file_path:
            self.input_file.set(file_path)
            self.show_video_info(file_path)

    def select_output_dir(self):
        dir_path = filedialog.askdirectory(title="Выберите папку для сохранения")
        if dir_path:
            self.output_dir.set(dir_path)

    def show_video_info(self, video_path):
        try:
            cmd = [
                'ffprobe', '-v', 'error', '-show_entries',
                'format=duration,size', '-of', 'default=noprint_wrappers=1',
                video_path
            ]
            result = subprocess.check_output(cmd, text=True)

            duration_sec = None
            size_bytes = None

            for line in result.split('\n'):
                if 'duration=' in line:
                    duration_sec = float(line.split('=')[1])
                elif 'size=' in line:
                    size_bytes = int(line.split('=')[1])

            if duration_sec:
                hours = int(duration_sec // 3600)
                minutes = int((duration_sec % 3600) // 60)
                seconds = int(duration_sec % 60)

                size_mb = size_bytes / (1024 * 1024) if size_bytes else 0
                seg_dur = int(self.segment_duration.get())
                num_segments = int(duration_sec // seg_dur) + (1 if duration_sec % seg_dur else 0)

                info = f"Длительность: {hours:02d}:{minutes:02d}:{seconds:02d}\n"
                info += f"Размер файла: {size_mb:.1f} MB\n"
                info += f"Будет создано сегментов: {num_segments}\n"

                self.update_info_text(info)
        except Exception as e:
            self.update_info_text(f"Ошибка: {str(e)}\n\nУбедитесь, что FFmpeg установлен!")

    def update_info_text(self, text):
        self.info_text.config(state='normal')
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, text)
        self.info_text.config(state='disabled')

    def start_processing(self):
        if not self.input_file.get():
            messagebox.showerror("Ошибка", "Выберите исходное видео!")
            return
        if not self.output_dir.get():
            messagebox.showerror("Ошибка", "Выберите папку для сохранения!")
            return
        try:
            duration = int(self.segment_duration.get())
            if duration < 1 or duration > 3600:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Длительность должна быть от 1 до 3600 секунд!")
            return

        self.process_btn.config(state='disabled', bg="#999", cursor="arrow")
        self.progress.start()
        threading.Thread(target=self.process_video, daemon=True).start()

    def process_video(self):
        try:
            input_file = self.input_file.get()
            output_dir = self.output_dir.get()
            duration = int(self.segment_duration.get())

            cmd_probe = [
                'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1', input_file
            ]
            total_duration = float(subprocess.check_output(cmd_probe).decode().strip())

            num_segments = int(total_duration // duration) + (1 if total_duration % duration else 0)

            base_name = Path(input_file).stem

            for i in range(num_segments):
                start_time = i * duration
                output_file = os.path.join(output_dir, f"{base_name}_part_{i + 1:03d}.mp4")

                self.root.after(0, lambda idx=i, total=num_segments: self.status_text.set(
                    f"Обработка {idx + 1}/{total}..."
                ))

                cmd = [
                    'ffmpeg', '-i', input_file, '-ss', str(start_time),
                    '-t', str(duration), '-c', 'copy', '-avoid_negative_ts', 'make_zero',
                    output_file, '-y'
                ]
                subprocess.run(cmd, check=True, capture_output=True)

            self.root.after(0, self.processing_finished)

        except Exception as e:
            self.root.after(0, lambda: self.processing_error(str(e)))

    def processing_finished(self):
        self.progress.stop()
        self.process_btn.config(state='normal', bg="#C04A4A", cursor="hand2")
        self.status_text.set("Готово! Видео успешно нарезано ✅")
        messagebox.showinfo("Успех", f"Видео нарезано!\nПапка: {self.output_dir.get()}")

    def processing_error(self, error_msg):
        self.progress.stop()
        self.process_btn.config(state='normal', bg="#C04A4A", cursor="hand2")
        self.status_text.set(f"Ошибка: {error_msg}")
        messagebox.showerror("Ошибка", f"Не удалось обработать:\n{error_msg}\n\nУбедитесь, что FFmpeg установлен!")

    def on_closing(self):
        """Чистое закрытие программы"""
        self.root.destroy()


def main():
    root = tk.Tk()
    root.iconbitmap("icon.ico")  # ← ДОБАВЛЕНА ИКОНКА
    app = VideoSplitterApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()