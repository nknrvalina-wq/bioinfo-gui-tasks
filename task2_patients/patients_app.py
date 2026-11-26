import json       # Модуль для чтения и записи данных в формате JSON (наш файл базы пациентов)
import os         # Модуль для работы с путями и проверки существования файлов
import tkinter as tk  # Основная библиотека графического интерфейса
from tkinter import messagebox, ttk  # messagebox - всплывающие окна ошибок/подтверждений; ttk - современные виджеты (таблица, выпадающий список, кнопки)

# Импорты для встраивания графиков matplotlib внутрь окна Tkinter:
# FigureCanvasTkAgg - "мост", превращающий график matplotlib в виджет Tkinter
# NavigationToolbar2Tk - стандартная панель matplotlib под графиком (лупа, перетаскивание, сохранение PNG)
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
# Figure - сам "холст" для рисования графиков (используем его вместо plt, чтобы не открывать лишнее окно)
from matplotlib.figure import Figure

# __file__ - путь к текущему файлу скрипта (patients_app.py).
# os.path.abspath(__file__) - превращаем его в полный абсолютный путь.
# os.path.dirname(...) - отрезаем имя файла и оставляем только папку, где лежит скрипт.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Склеиваем путь к папке скрипта и имя файла "patients.json".
# Благодаря этому файл данных ВСЕГДА будет лежать рядом со скриптом, из какой бы папки вы его ни запустили.
DATA_FILE = os.path.join(BASE_DIR, "patients.json")


def calculate_bmi(height_cm: float, weight_kg: float) -> float:
    """Расчёт индекса массы тела: вес(кг) / рост(м)^2."""
    height_m = height_cm / 100.0                 # Переводим рост из сантиметров в метры
    return round(weight_kg / (height_m ** 2), 2) # Считаем ИМТ и округляем до 2 знаков после запятой


# =============================================================================
# ОКНО ДОБАВЛЕНИЯ И РЕДАКТИРОВАНИЯ ПАЦИЕНТА
# =============================================================================
class PatientDialog(tk.Toplevel):
    """Всплывающее (дочернее) окно для ввода или изменения данных одного пациента.
    Наследуется от tk.Toplevel - это значит, что сам объект этого класса является окном.
    """

    def __init__(self, parent, title: str, initial_data: dict | None = None):
        # Вызываем конструктор родительского класса tk.Toplevel,
        # передавая ему parent (главное окно), чтобы новое окно знало, кто его открыл.
        super().__init__(parent)

        self.title(title)              # Заголовок в шапке всплывающего окна ("Добавить..." или "Редактировать...")
        self.geometry("380x290")       # Начальный размер окна: ширина 380px, высота 290px
        self.resizable(False, False)   # Запрещаем пользователю растягивать это окно мышкой
        self.configure(bg="#F8FAFC")   # Задаём светло-серый фон окна

        # Делаем окно "привязанным" к главному:
        # 1) transient(parent) - окно всегда будет поверх главного окна и не создаст лишнюю иконку на панели задач
        # 2) grab_set() - модальный режим: пока форма открыта, кликать по таблице в главном окне нельзя
        self.transient(parent)
        self.grab_set()

        # Сюда запишем словарь с готовыми данными пациента, когда пользователь нажмёт "Сохранить".
        # Если нажмёт "Отмена" или крестик - здесь останется None.
        self.result: dict | None = None

        # Если передали данные существующего пациента (режим редактирования) - берём их.
        # Если передали None (режим добавления) - берём пустой словарь {}.
        data = initial_data or {}

        # Создаём внутреннюю рамку-контейнер с отступами от краёв окна (padx=16, pady=16)
        frame = tk.Frame(self, bg="#F8FAFC", padx=16, pady=16)
        frame.pack(fill="both", expand=True)  # Растягиваем рамку на всё окно

        # --- Поле 1: ФИО ---
        # Создаём подпись в строке 0, столбце 0 (sticky="w" - прижать текст влево)
        tk.Label(frame, text="ФИО:", bg="#F8FAFC", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=6)
        # Создаём реактивную строковую переменную; если редактируем - сразу кладём старое ФИО, иначе ""
        self.name_var = tk.StringVar(value=data.get("full_name", ""))
        # Создаём текстовое поле Entry, привязываем к self.name_var и ставим в строку 0, столбец 1
        # sticky="ew" - растягиваем поле по горизонтали (East-West) на всю ширину столбца
        ttk.Entry(frame, textvariable=self.name_var, width=28).grid(row=0, column=1, sticky="ew", pady=6)

        # --- Поле 2: Возраст ---
        tk.Label(frame, text="Возраст (лет):", bg="#F8FAFC", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=6)
        # age в словаре - это int, а StringVar принимает только строку str, поэтому оборачиваем в str(...)
        self.age_var = tk.StringVar(value=str(data.get("age", "")))
        ttk.Entry(frame, textvariable=self.age_var, width=28).grid(row=1, column=1, sticky="ew", pady=6)

        # --- Поле 3: Пол (выпадающий список) ---
        tk.Label(frame, text="Пол:", bg="#F8FAFC", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=6)
        self.gender_var = tk.StringVar(value=data.get("gender", "Мужской"))  # По умолчанию выбран "Мужской"
        ttk.Combobox(
            frame,
            textvariable=self.gender_var,     # Привязываем выбранное значение к переменной
            values=("Мужской", "Женский"),    # Список вариантов для выбора
            state="readonly",                 # Запрещаем печатать свой текст руками (только выбор из списка)
            width=26,
        ).grid(row=2, column=1, sticky="ew", pady=6)

        # --- Поле 4: Рост ---
        tk.Label(frame, text="Рост (см):", bg="#F8FAFC", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="w", pady=6)
        self.height_var = tk.StringVar(value=str(data.get("height", "")))
        ttk.Entry(frame, textvariable=self.height_var, width=28).grid(row=3, column=1, sticky="ew", pady=6)

        # --- Поле 5: Вес ---
        tk.Label(frame, text="Вес (кг):", bg="#F8FAFC", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky="w", pady=6)
        self.weight_var = tk.StringVar(value=str(data.get("weight", "")))
        ttk.Entry(frame, textvariable=self.weight_var, width=28).grid(row=4, column=1, sticky="ew", pady=6)

        # Разрешаем столбцу 1 (где находятся поля ввода) растягиваться на всё свободное место по ширине
        frame.columnconfigure(1, weight=1)

        # Контейнер для двух кнопок внизу ("Отмена" и "Сохранить")
        btn_frame = tk.Frame(frame, bg="#F8FAFC")
        # Ставим в 5-ю строку, объединяем 2 столбца (columnspan=2), прижимаем к правому краю (sticky="e")
        btn_frame.grid(row=5, column=0, columnspan=2, pady=(18, 0), sticky="e")

        # Кнопка "Отмена": просто уничтожает (закрывает) окно, self.result остаётся None
        ttk.Button(btn_frame, text="Отмена", command=self.destroy).pack(side="right", padx=(8, 0))
        # Кнопка "Сохранить": запускает проверку полей и сохранение результата
        ttk.Button(btn_frame, text="Сохранить", command=self._on_save).pack(side="right")

        # При нажатии Enter на клавиатуре также вызываем сохранение
        self.bind("<Return>", lambda _e: self._on_save())

    def _on_save(self):
        """Проверяет введённые поля; если всё верно - сохраняет словарь в self.result и закрывает окно."""
        try:
            # Читаем ФИО из поля и убираем пробелы по краям
            full_name = self.name_var.get().strip()
            if not full_name:
                raise ValueError("Введите ФИО пациента")  # Выбрасываем исключение, если строка пустая

            # Пробуем превратить возраст в целое число (если там буквы - int() сам выбросит ValueError)
            age = int(self.age_var.get().strip())
            if not (1 <= age <= 130):
                raise ValueError("Возраст должен быть от 1 до 130 лет")

            gender = self.gender_var.get()
            if gender not in ("Мужской", "Женский"):
                raise ValueError("Выберите пол")

            # Заменяем запятую на точку (на случай русской раскладки) и превращаем в дробное число
            height = float(self.height_var.get().strip().replace(",", "."))
            if not (30 <= height <= 260):
                raise ValueError("Рост должен быть от 30 до 260 см")

            weight = float(self.weight_var.get().strip().replace(",", "."))
            if not (2 <= weight <= 400):
                raise ValueError("Вес должен быть от 2 до 400 кг")

            # Если все проверки прошли - формируем итоговый словарь пациента и считаем ИМТ
            self.result = {
                "full_name": full_name,
                "age": age,
                "gender": gender,
                "height": round(height, 1),
                "weight": round(weight, 1),
                "bmi": calculate_bmi(height, weight),
            }
            # Закрываем окно диалога (после этого в главном окне закончится ожидание wait_window)
            self.destroy()
        except ValueError as err:
            # Если на каком-то этапе возникла ошибка валидации - показываем всплывающее окно с ошибкой.
            # parent=self гарантирует, что окно ошибки появится поверх диалога, а не под ним.
            messagebox.showerror("Ошибка ввода", str(err), parent=self)


# =============================================================================
# ОКНО СВОДНОЙ СТАТИСТИКИ (4 ГРАФИКА)
# =============================================================================
class StatsWindow(tk.Toplevel):
    """Отдельное окно, в которое встроены 4 статистических графика matplotlib."""

    def __init__(self, parent, patients: list[dict]):
        super().__init__(parent)  # Инициализируем дочернее окно tk.Toplevel
        self.title("Сводная статистика по пациентам")
        self.geometry("1000x740")
        self.minsize(820, 620)

        # Создаём объект фигуры matplotlib размером 10x7.2 дюйма при плотности 100 точек/дюйм (~1000x720 px)
        fig = Figure(figsize=(10, 7.2), dpi=100)

        # Делим всех пациентов на два списка по полу, чтобы удобно строить графики
        male_pts = [p for p in patients if p["gender"] == "Мужской"]
        female_pts = [p for p in patients if p["gender"] == "Женский"]

        # --- График 1 (левый верх): Распределение пациентов по полу ---
        # add_subplot(2, 2, 1) означает: сетка 2 строки x 2 столбца, выбрать 1-ю ячейку
        ax1 = fig.add_subplot(2, 2, 1)
        counts = [len(male_pts), len(female_pts)]  # Сколько мужчин и сколько женщин
        # Рисуем столбчатую диаграмму (bar): названия по X, высоты столбцов, цвета, ширина столбца
        bars = ax1.bar(["Мужской", "Женский"], counts, color=["#3B82F6", "#EC4899"], width=0.5)
        ax1.set_title("Распределение пациентов по полу")
        ax1.set_ylabel("Количество пациентов")
        ax1.grid(axis="y", alpha=0.3)  # Полупрозрачная горизонтальная сетка
        # Подписываем точные числа прямо над каждым столбиком
        for bar, cnt in zip(bars, counts):
            # bar.get_x() + bar.get_width() / 2 - точная координата середины столбика по X
            # cnt + 0.1 - чуть выше верхушки столбика по Y
            ax1.text(bar.get_x() + bar.get_width() / 2, cnt + 0.1, str(cnt), ha="center", va="bottom")

        # --- График 2 (правый верх): Распределение пациентов по возрасту ---
        ax2 = fig.add_subplot(2, 2, 2)  # 2-я ячейка сетки 2x2
        ages = [p["age"] for p in patients]  # Собираем список возрастов всех пациентов
        # Рисуем гистограмму (hist); bins="auto" - matplotlib сам подберёт количество столбцов
        ax2.hist(ages, bins="auto", color="#10B981", edgecolor="white")
        ax2.set_title("Распределение пациентов по возрасту")
        ax2.set_xlabel("Возраст (лет)")
        ax2.set_ylabel("Количество")
        ax2.grid(axis="y", alpha=0.3)

        # --- График 3 (левый низ): Распределение ИМТ с учётом пола ---
        ax3 = fig.add_subplot(2, 2, 3)  # 3-я ячейка сетки 2x2
        bmi_groups = []   # Сюда положим списки ИМТ для каждой непустой группы
        bmi_labels = []   # Сюда положим подписи групп ("Мужской", "Женский")
        box_colors = []   # Сюда положим цвета коробок для каждой группы

        # Проверяем, что группа не пустая (на случай, если в базе только один пол)
        if male_pts:
            bmi_groups.append([p["bmi"] for p in male_pts])
            bmi_labels.append("Мужской")
            box_colors.append("#93C5FD")
        if female_pts:
            bmi_groups.append([p["bmi"] for p in female_pts])
            bmi_labels.append("Женский")
            box_colors.append("#F9A8D4")

        # Рисуем диаграмму "ящик с усами" (boxplot).
        # patch_artist=True ОБЯЗАТЕЛЕН, чтобы ящики можно было закрасить цветом внутри.
        bp = ax3.boxplot(bmi_groups, patch_artist=True)
        # Перебираем прямоугольники ящиков (bp["boxes"]) и красим их в нужные цвета
        for patch, color in zip(bp["boxes"], box_colors):
            patch.set_facecolor(color)
        ax3.set_xticklabels(bmi_labels)  # Ставим подписи под ящиками на оси X
        ax3.set_title("Распределение ИМТ с учётом пола")
        ax3.set_ylabel("ИМТ")
        ax3.grid(axis="y", alpha=0.3)

        # --- График 4 (правый низ): Зависимость ИМТ от возраста ---
        ax4 = fig.add_subplot(2, 2, 4)  # 4-я ячейка сетки 2x2
        # Рисуем точки (scatter) отдельно для мужчин (синие) и женщин (розовые), чтобы показать легенду
        if male_pts:
            ax4.scatter(
                [p["age"] for p in male_pts],  # Координаты X (возраст)
                [p["bmi"] for p in male_pts],  # Координаты Y (ИМТ)
                color="#3B82F6",
                label="Мужской",               # Подпись для легенды
                alpha=0.8,                     # Небольшая прозрачность точек
                s=50,                          # Размер точек
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
        ax4.legend()           # Показываем легенду (синие = Мужской, розовые = Женский)
        ax4.grid(alpha=0.3)

        # Автоматически подбираем отступы между 4 графиками, чтобы заголовки не налезали друг на друга
        fig.tight_layout(pad=2.0)

        # Создаём виджет-холст Tkinter из нашей фигуры matplotlib (master=self - кладём прямо в это окно)
        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.draw()  # Отрисовываем фигуру на холсте

        # Добавляем стандартную панель инструментов matplotlib (масштаб, перетаскивание, сохранить PNG)
        toolbar = NavigationToolbar2Tk(canvas, self)
        toolbar.update()

        # Получаем сам Tkinter-виджет холста (get_tk_widget()) и растягиваем его на всё окно
        canvas.get_tk_widget().pack(fill="both", expand=True)


# =============================================================================
# ГЛАВНОЕ ОКНО ПРИЛОЖЕНИЯ (ТАБЛИЦА + КНОПКИ УПРАВЛЕНИЯ)
# =============================================================================
class PatientsApp:
    def __init__(self, root: tk.Tk):
        self.root = root                       # Сохраняем ссылку на главное окно tk.Tk()
        self.root.title("Учёт пациентов")      # Заголовок главного окна
        self.root.geometry("920x540")          # Начальный размер окна
        self.root.minsize(760, 440)            # Минимальный размер окна (чтобы кнопки не пропадали)
        self.root.configure(bg="#F1F5F9")      # Светло-серый фон

        self.patients: list[dict] = []         # Главный список словарей пациентов в памяти программы
        self._setup_styles()                   # Настраиваем внешний вид таблицы и кнопок ttk
        self._build_ui()                       # Строим все элементы окна
        self.load_patients()                   # При старте сразу пытаемся загрузить сохранённых пациентов из файла

    def _setup_styles(self):
        """Настройка стилей ttk-виджетов (тема, шрифты, цвета кнопок и таблицы)."""
        style = ttk.Style()
        style.theme_use("clam")  # Тема 'clam' одинаково красиво красит кнопки на Windows, macOS и Linux

        # Настраиваем шрифт и высоту строк (rowheight=28px) для таблицы Treeview
        style.configure("Treeview", font=("Arial", 10), rowheight=28)
        # Настраиваем шрифт и фон шапки таблицы
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background="#E2E8F0")

        # Стиль для главных синих кнопок ("+ Добавить" и "Сводная статистика")
        style.configure("Primary.TButton", font=("Arial", 10, "bold"), padding=(12, 6), background="#2563EB", foreground="#FFFFFF")
        style.map("Primary.TButton", background=[("active", "#1D4ED8")])  # Темнее при наведении

        # Стиль для обычных кнопок ("Редактировать", "Удалить", "Faker")
        style.configure("Regular.TButton", font=("Arial", 10), padding=(10, 6))

    def _build_ui(self):
        """Создаёт и расставляет все элементы главного окна."""
        # --- Верхний заголовок ---
        header = tk.Frame(self.root, bg="#F1F5F9", padx=16, pady=12)
        header.pack(fill="x")

        tk.Label(
            header,
            text="База данных пациентов",
            font=("Arial", 16, "bold"),
            bg="#F1F5F9",
            fg="#0F172A",
        ).pack(side="left")  # Прижимаем текст заголовка к левому краю

        # --- Панель с кнопками ---
        btn_bar = tk.Frame(self.root, bg="#F1F5F9", padx=16, pady=4)
        btn_bar.pack(fill="x")

        # Кнопки слева выстраиваются в ряд одна за другой (side="left")
        ttk.Button(btn_bar, text="+ Добавить пациента", style="Primary.TButton", command=self.add_patient).pack(side="left", padx=(0, 8))
        ttk.Button(btn_bar, text="Редактировать", style="Regular.TButton", command=self.edit_patient).pack(side="left", padx=(0, 8))
        ttk.Button(btn_bar, text="Удалить", style="Regular.TButton", command=self.delete_patient).pack(side="left", padx=(0, 8))
        ttk.Button(btn_bar, text="Сгенерировать 5 (Faker)", style="Regular.TButton", command=self.generate_faker_patients).pack(side="left", padx=(0, 8))
        # Кнопку статистики прижимаем к правому краю (side="right")
        ttk.Button(btn_bar, text="Сводная статистика", style="Primary.TButton", command=self.show_stats).pack(side="right")

        # --- Контейнер для таблицы и полосы прокрутки ---
        table_frame = tk.Frame(self.root, bg="#F1F5F9", padx=16, pady=12)
        table_frame.pack(fill="both", expand=True)  # Таблица забирает всё оставшееся место при растяжении окна

        # Внутренние имена (ключи) 6 столбцов таблицы
        columns = ("full_name", "age", "gender", "height", "weight", "bmi")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,      # Передаём кортеж столбцов
            show="headings",      # Прячем левый технический столбец-дерево (#0), оставляем только таблицу
            selectmode="browse",  # Пользователь может выделить одновременно только 1 строку
        )

        # Словарь настроек каждого столбца: ключ -> (Текст шапки, Ширина в px, Выравнивание данных)
        headings = {
            "full_name": ("ФИО", 260, "w"),          # "w" - выравнивание текста по левому краю
            "age": ("Возраст", 80, "center"),
            "gender": ("Пол", 110, "center"),
            "height": ("Рост (см)", 100, "center"),
            "weight": ("Вес (кг)", 100, "center"),
            "bmi": ("ИМТ", 90, "center"),
        }
        # Проходимся по словарю и настраиваем шапку и колонку для каждого столбца
        for col, (title, width, anchor) in headings.items():
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor=anchor)

        # Создаём вертикальную полосу прокрутки и соединяем её с таблицей в обе стороны:
        # 1) command=self.tree.yview - ползунок крутит таблицу вверх/вниз
        # 2) yscrollcommand=scrollbar.set - таблица двигает ползунок при прокрутке колёсиком мыши
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Кладём таблицу слева (на всё свободное место), а скроллбар справа (тянется только по Y)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Вешаем событие двойного клика левой кнопкой мыши (<Double-1>) на таблицу -> открывает редактирование
        self.tree.bind("<Double-1>", lambda _e: self.edit_patient())

        # --- Нижняя строка состояния ---
        self.status_var = tk.StringVar(value="Всего пациентов: 0")
        tk.Label(
            self.root,
            textvariable=self.status_var,  # Автоматически обновляется при изменении self.status_var
            bg="#E2E8F0",
            fg="#334155",
            font=("Arial", 9),
            anchor="w",
            padx=16,
            pady=6,
        ).pack(fill="x")

    def refresh_table(self):
        """Полностью перерисовывает таблицу на основе актуального списка self.patients."""
        # get_children() возвращает все ID текущих строк; удаляем их перед повторным заполнением
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Вставляем всех пациентов заново
        for idx, p in enumerate(self.patients):
            self.tree.insert(
                "",            # "" - строка верхнего уровня (без вложенности)
                "end",         # Добавляем в конец таблицы
                iid=str(idx),  # ВАЖНО: в качестве ID строки записываем индекс пациента в списке self.patients
                values=(p["full_name"], p["age"], p["gender"], p["height"], p["weight"], p["bmi"]),
            )
        # Обновляем счётчик внизу окна
        self.status_var.set(f"Всего пациентов: {len(self.patients)}  |  Файл: {os.path.basename(DATA_FILE)}")

    def load_patients(self):
        """Загружает список пациентов из файла patients.json при запуске программы."""
        if os.path.exists(DATA_FILE):  # Проверяем, существует ли файл на диске
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.patients = json.load(f)  # Превращаем JSON-текст в список словарей Python
            except (OSError, json.JSONDecodeError) as err:
                # Если файл повреждён или нет прав на чтение - показываем предупреждение, не падаем
                messagebox.showwarning("Предупреждение", f"Не удалось прочитать файл данных: {err}")
                self.patients = []
        self.refresh_table()  # Отрисовываем загруженные данные в таблице

    def save_patients(self):
        """Сохраняет текущий список self.patients в файл patients.json."""
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                # ensure_ascii=False - сохраняет русские буквы как есть (не в виде \uXXXX)
                # indent=2 - красивое форматирование с отступами
                json.dump(self.patients, f, ensure_ascii=False, indent=2)
        except OSError as err:
            messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить данные: {err}")

    def add_patient(self):
        """Обработчик кнопки '+ Добавить пациента'."""
        dialog = PatientDialog(self.root, "Добавить пациента")  # Открываем пустое окно формы
        self.root.wait_window(dialog)                           # Ставим код на паузу, пока окно формы не закроется
        if dialog.result:                                       # Если пользователь нажал "Сохранить" (result не None)
            self.patients.append(dialog.result)                 # Добавляем нового пациента в список
            self.save_patients()                                # Записываем обновлённый список в файл
            self.refresh_table()                                # Перерисовываем таблицу

    def edit_patient(self):
        """Обработчик кнопки 'Редактировать' и двойного клика по строке."""
        selected = self.tree.selection()  # Получаем кортеж выделенных строк, например ('2',) или ()
        if not selected:                  # Если ни одна строка не выделена - просим выбрать
            messagebox.showinfo("Выбор пациента", "Выберите пациента в таблице для редактирования.")
            return

        # Мы при вставке записали индекс пациента в iid строки, поэтому достаём его обратно
        idx = int(selected[0])
        # Открываем диалог, передав третьим аргументом старый словарь self.patients[idx] для предзаполнения полей
        dialog = PatientDialog(self.root, "Редактировать пациента", self.patients[idx])
        self.root.wait_window(dialog)  # Ждём закрытия формы
        if dialog.result:
            self.patients[idx] = dialog.result  # Заменяем данные пациента под тем же индексом
            self.save_patients()
            self.refresh_table()

    def delete_patient(self):
        """Обработчик кнопки 'Удалить'."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Выбор пациента", "Выберите пациента в таблице для удаления.")
            return

        idx = int(selected[0])
        name = self.patients[idx]["full_name"]
        # askyesno возвращает True (нажали "Да") или False (нажали "Нет")
        if messagebox.askyesno("Подтверждение", f"Удалить пациента «{name}»?"):
            self.patients.pop(idx)  # Удаляем пациента из списка по индексу
            self.save_patients()
            self.refresh_table()

    def generate_faker_patients(self):
        """Генерирует 5 случайных пациентов через библиотеку faker (если она установлена)."""
        try:
            import random
            from faker import Faker
        except ImportError:
            messagebox.showerror("Библиотека не найдена", "Установите библиотеку faker: pip install faker")
            return

        fake = Faker("ru_RU")  # Создаём генератор русскоязычных данных
        for _ in range(5):
            gender = random.choice(["Мужской", "Женский"])
            # Выбираем мужское или женское ФИО в зависимости от выпавшего пола
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
        """Обработчик кнопки 'Сводная статистика'."""
        if not self.patients:
            messagebox.showinfo("Нет данных", "Список пациентов пуст. Добавьте хотя бы одного пациента.")
            return
        # Открываем окно StatsWindow и передаём ему текущий список пациентов
        StatsWindow(self.root, self.patients)


# Точка входа: этот блок выполняется, только если файл запущен напрямую (а не импортирован)
if __name__ == "__main__":
    root = tk.Tk()       # Создаём главное окно приложения
    PatientsApp(root)    # Создаём наш интерфейс внутри этого окна
    root.mainloop()      # Запускаем цикл обработки событий (ждёт кликов и не закрывает окно)