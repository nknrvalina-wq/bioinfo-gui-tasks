import json
import os
import tkinter as tk
from tkinter import messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

# Файл данных хранится рядом со скриптом (работает из любой директории)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "patients.json")


def calculate_bmi(height_cm: float, weight_kg: float) -> float:
    """Расчёт индекса массы тела: вес(кг) / рост(м)^2."""
    height_m = height_cm / 100.0
    return round(weight_kg / (height_m ** 2), 2)


class PatientDialog(tk.Toplevel):
    """Окно для добавления или редактирования одного пациента."""

    def __init__(self, parent, title: str, initial_data: dict | None = None):
        super().__init__(parent)
        self.title(title)
        self.geometry("380x290")
        self.resizable(False, False)
        self.configure(bg="#F8FAFC")
        self.transient(parent)
        self.grab_set()

        self.result: dict | None = None
        data = initial_data or {}

        frame = tk.Frame(self, bg="#F8FAFC", padx=16, pady=16)
        frame.pack(fill="both", expand=True)

        # Поля формы
        tk.Label(frame, text="ФИО:", bg="#F8FAFC", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=6)
        self.name_var = tk.StringVar(value=data.get("full_name", ""))
        ttk.Entry(frame, textvariable=self.name_var, width=28).grid(row=0, column=1, sticky="ew", pady=6)

        tk.Label(frame, text="Возраст (лет):", bg="#F8FAFC", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=6)
        self.age_var = tk.StringVar(value=str(data.get("age", "")))
        ttk.Entry(frame, textvariable=self.age_var, width=28).grid(row=1, column=1, sticky="ew", pady=6)

        tk.Label(frame, text="Пол:", bg="#F8FAFC", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=6)
        self.gender_var = tk.StringVar(value=data.get("gender", "Мужской"))
        ttk.Combobox(
            frame,
            textvariable=self.gender_var,
            values=("Мужской", "Женский"),
            state="readonly",
            width=26,
        ).grid(row=2, column=1, sticky="ew", pady=6)

        tk.Label(frame, text="Рост (см):", bg="#F8FAFC", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="w", pady=6)
        self.height_var = tk.StringVar(value=str(data.get("height", "")))
        ttk.Entry(frame, textvariable=self.height_var, width=28).grid(row=3, column=1, sticky="ew", pady=6)

        tk.Label(frame, text="Вес (кг):", bg="#F8FAFC", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky="w", pady=6)
        self.weight_var = tk.StringVar(value=str(data.get("weight", "")))
        ttk.Entry(frame, textvariable=self.weight_var, width=28).grid(row=4, column=1, sticky="ew", pady=6)

        frame.columnconfigure(1, weight=1)

        btn_frame = tk.Frame(frame, bg="#F8FAFC")
        btn_frame.grid(row=5, column=0, columnspan=2, pady=(18, 0), sticky="e")

        ttk.Button(btn_frame, text="Отмена", command=self.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(btn_frame, text="Сохранить", command=self._on_save).pack(side="right")

        self.bind("<Return>", lambda _e: self._on_save())

    def _on_save(self):
        try:
            full_name = self.name_var.get().strip()
            if not full_name:
                raise ValueError("Введите ФИО пациента")

            age = int(self.age_var.get().strip())
            if not (1 <= age <= 130):
                raise ValueError("Возраст должен быть от 1 до 130 лет")

            gender = self.gender_var.get()
            if gender not in ("Мужской", "Женский"):
                raise ValueError("Выберите пол")

            height = float(self.height_var.get().strip().replace(",", "."))
            if not (30 <= height <= 260):
                raise ValueError("Рост должен быть от 30 до 260 см")

            weight = float(self.weight_var.get().strip().replace(",", "."))
            if not (2 <= weight <= 400):
                raise ValueError("Вес должен быть от 2 до 400 кг")

            self.result = {
                "full_name": full_name,
                "age": age,
                "gender": gender,
                "height": round(height, 1),
                "weight": round(weight, 1),
                "bmi": calculate_bmi(height, weight),
            }
            self.destroy()
        except ValueError as err:
            messagebox.showerror("Ошибка ввода", str(err), parent=self)


class StatsWindow(tk.Toplevel):
    """Окно со сводной статистикой (4 графика)."""

    def __init__(self, parent, patients: list[dict]):
        super().__init__(parent)
        self.title("Сводная статистика по пациентам")
        self.geometry("1000x740")
        self.minsize(820, 620)

        fig = Figure(figsize=(10, 7.2), dpi=100)

        male_pts = [p for p in patients if p["gender"] == "Мужской"]
        female_pts = [p for p in patients if p["gender"] == "Женский"]

        # 1. Распределение по полу
        ax1 = fig.add_subplot(2, 2, 1)
        counts = [len(male_pts), len(female_pts)]
        bars = ax1.bar(["Мужской", "Женский"], counts, color=["#3B82F6", "#EC4899"], width=0.5)
        ax1.set_title("Распределение пациентов по полу")
        ax1.set_ylabel("Количество пациентов")
        ax1.grid(axis="y", alpha=0.3)
        for bar, cnt in zip(bars, counts):
            ax1.text(bar.get_x() + bar.get_width() / 2, cnt + 0.1, str(cnt), ha="center", va="bottom")

        # 2. Распределение по возрасту
        ax2 = fig.add_subplot(2, 2, 2)
        ages = [p["age"] for p in patients]
        ax2.hist(ages, bins="auto", color="#10B981", edgecolor="white")
        ax2.set_title("Распределение пациентов по возрасту")
        ax2.set_xlabel("Возраст (лет)")
        ax2.set_ylabel("Количество")
        ax2.grid(axis="y", alpha=0.3)

        # 3. Распределение ИМТ с учётом пола
        ax3 = fig.add_subplot(2, 2, 3)
        bmi_groups = []
        bmi_labels = []
        box_colors = []
        if male_pts:
            bmi_groups.append([p["bmi"] for p in male_pts])
            bmi_labels.append("Мужской")
            box_colors.append("#93C5FD")
        if female_pts:
            bmi_groups.append([p["bmi"] for p in female_pts])
            bmi_labels.append("Женский")
            box_colors.append("#F9A8D4")

        bp = ax3.boxplot(bmi_groups, patch_artist=True)
        for patch, color in zip(bp["boxes"], box_colors):
            patch.set_facecolor(color)
        ax3.set_xticklabels(bmi_labels)
        ax3.set_title("Распределение ИМТ с учётом пола")
        ax3.set_ylabel("ИМТ")
        ax3.grid(axis="y", alpha=0.3)

        # 4. Зависимость ИМТ от возраста
        ax4 = fig.add_subplot(2, 2, 4)
        if male_pts:
            ax4.scatter(
                [p["age"] for p in male_pts],
                [p["bmi"] for p in male_pts],
                color="#3B82F6",
                label="Мужской",
                alpha=0.8,
                s=50,
            )
        if female_pts:
            ax4.scatter(
                [p["age"] for p in female_pts],
                [p["bmi"] for p in female_pts],
                color="#EC4899",
                label="Женский",
                alpha=0.8,
                s=50,
            )
        ax4.set_title("Зависимость ИМТ от возраста")
        ax4.set_xlabel("Возраст (лет)")
        ax4.set_ylabel("ИМТ")
        ax4.legend()
        ax4.grid(alpha=0.3)

        fig.tight_layout(pad=2.0)

        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.draw()
        toolbar = NavigationToolbar2Tk(canvas, self)
        toolbar.update()
        canvas.get_tk_widget().pack(fill="both", expand=True)


class PatientsApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Учёт пациентов")
        self.root.geometry("920x540")
        self.root.minsize(760, 440)
        self.root.configure(bg="#F1F5F9")

        self.patients: list[dict] = []
        self._setup_styles()
        self._build_ui()
        self.load_patients()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=("Arial", 10), rowheight=28)
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background="#E2E8F0")
        style.configure("Primary.TButton", font=("Arial", 10, "bold"), padding=(12, 6), background="#2563EB", foreground="#FFFFFF")
        style.map("Primary.TButton", background=[("active", "#1D4ED8")])
        style.configure("Regular.TButton", font=("Arial", 10), padding=(10, 6))

    def _build_ui(self):
        # Заголовок и панель кнопок
        header = tk.Frame(self.root, bg="#F1F5F9", padx=16, pady=12)
        header.pack(fill="x")

        tk.Label(
            header,
            text="База данных пациентов",
            font=("Arial", 16, "bold"),
            bg="#F1F5F9",
            fg="#0F172A",
        ).pack(side="left")

        btn_bar = tk.Frame(self.root, bg="#F1F5F9", padx=16, pady=4)
        btn_bar.pack(fill="x")

        ttk.Button(btn_bar, text="+ Добавить пациента", style="Primary.TButton", command=self.add_patient).pack(side="left", padx=(0, 8))
        ttk.Button(btn_bar, text="Редактировать", style="Regular.TButton", command=self.edit_patient).pack(side="left", padx=(0, 8))
        ttk.Button(btn_bar, text="Удалить", style="Regular.TButton", command=self.delete_patient).pack(side="left", padx=(0, 8))
        ttk.Button(btn_bar, text="Сгенерировать 5 (Faker)", style="Regular.TButton", command=self.generate_faker_patients).pack(side="left", padx=(0, 8))
        ttk.Button(btn_bar, text="Сводная статистика", style="Primary.TButton", command=self.show_stats).pack(side="right")

        # Таблица пациентов
        table_frame = tk.Frame(self.root, bg="#F1F5F9", padx=16, pady=12)
        table_frame.pack(fill="both", expand=True)

        columns = ("full_name", "age", "gender", "height", "weight", "bmi")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        headings = {
            "full_name": ("ФИО", 260, "w"),
            "age": ("Возраст", 80, "center"),
            "gender": ("Пол", 110, "center"),
            "height": ("Рост (см)", 100, "center"),
            "weight": ("Вес (кг)", 100, "center"),
            "bmi": ("ИМТ", 90, "center"),
        }
        for col, (title, width, anchor) in headings.items():
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor=anchor)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Двойной клик по строке открывает редактирование
        self.tree.bind("<Double-1>", lambda _e: self.edit_patient())

        # Строка состояния внизу
        self.status_var = tk.StringVar(value="Всего пациентов: 0")
        tk.Label(
            self.root,
            textvariable=self.status_var,
            bg="#E2E8F0",
            fg="#334155",
            font=("Arial", 9),
            anchor="w",
            padx=16,
            pady=6,
        ).pack(fill="x")

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for idx, p in enumerate(self.patients):
            self.tree.insert(
                "",
                "end",
                iid=str(idx),
                values=(p["full_name"], p["age"], p["gender"], p["height"], p["weight"], p["bmi"]),
            )
        self.status_var.set(f"Всего пациентов: {len(self.patients)}  |  Файл: {os.path.basename(DATA_FILE)}")

    def load_patients(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.patients = json.load(f)
            except (OSError, json.JSONDecodeError) as err:
                messagebox.showwarning("Предупреждение", f"Не удалось прочитать файл данных: {err}")
                self.patients = []
        self.refresh_table()

    def save_patients(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.patients, f, ensure_ascii=False, indent=2)
        except OSError as err:
            messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить данные: {err}")

    def add_patient(self):
        dialog = PatientDialog(self.root, "Добавить пациента")
        self.root.wait_window(dialog)
        if dialog.result:
            self.patients.append(dialog.result)
            self.save_patients()
            self.refresh_table()

    def edit_patient(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Выбор пациента", "Выберите пациента в таблице для редактирования.")
            return

        idx = int(selected[0])
        dialog = PatientDialog(self.root, "Редактировать пациента", self.patients[idx])
        self.root.wait_window(dialog)
        if dialog.result:
            self.patients[idx] = dialog.result
            self.save_patients()
            self.refresh_table()

    def delete_patient(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Выбор пациента", "Выберите пациента в таблице для удаления.")
            return

        idx = int(selected[0])
        name = self.patients[idx]["full_name"]
        if messagebox.askyesno("Подтверждение", f"Удалить пациента «{name}»?"):
            self.patients.pop(idx)
            self.save_patients()
            self.refresh_table()

    def generate_faker_patients(self):
        try:
            import random
            from faker import Faker
        except ImportError:
            messagebox.showerror("Библиотека не найдена", "Установите библиотеку faker: pip install faker")
            return

        fake = Faker("ru_RU")
        for _ in range(5):
            gender = random.choice(["Мужской", "Женский"])
            full_name = fake.name_male() if gender == "Мужской" else fake.name_female()
            age = random.randint(18, 80)
            height = round(random.uniform(155, 195), 1)
            weight = round(random.uniform(50, 110), 1)
            self.patients.append(
                {
                    "full_name": full_name,
                    "age": age,
                    "gender": gender,
                    "height": height,
                    "weight": weight,
                    "bmi": calculate_bmi(height, weight),
                }
            )
        self.save_patients()
        self.refresh_table()

    def show_stats(self):
        if not self.patients:
            messagebox.showinfo("Нет данных", "Список пациентов пуст. Добавьте хотя бы одного пациента.")
            return
        StatsWindow(self.root, self.patients)


if __name__ == "__main__":
    root = tk.Tk()
    PatientsApp(root)
    root.mainloop()