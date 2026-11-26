import math
import re
import tkinter as tk
from tkinter import ttk


def format_number(value: float) -> str: # делает красивые циферки
    if isinstance(value, complex):
        raise ValueError("Результат не является действительным числом")
    rounded = round(float(value), 10) 
    if rounded.is_integer(): # проверяем, есть ли после запятой знаки(целое ли число)
        return str(int(rounded)) 
    return str(rounded) 


def evaluate_expression(expr: str) -> float:
    """Проверяет выражение и безопасно вычисляет его значение."""
    expr = expr.strip().replace(",", ".")
    if not expr:
        raise ValueError("Введите выражение")

    # Разрешаем только цифры, пробелы, скобки и арифметические операторы
    if not re.fullmatch(r"[0-9+\-*/().\s]+", expr): # вопрос остается
        raise ValueError("Допустимы только цифры и знаки + - * / ( )")

    result = eval(expr, {"__builtins__": None}, {})
    if not isinstance(result, (int, float)):
        raise ValueError("Некорректный результат")
    return float(result)


class CalculatorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("✿ Калькулятор ✿")
        self.root.geometry("370x560")
        self.root.minsize(340, 520)
        self.root.configure(bg="#FFF0F5")  # нежно-розовый фон

        self._setup_styles()
        self._build_ui()
        self._bind_keyboard()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure( # создаем новую коробочку стилей для кнопок
            "Digit.TButton", # название
            font=("Arial", 14, "bold"), # шрифт
            padding=8, # внутренний отступ текста от краёв кнопки
            background="#FFFFFF", # Цвет фона в кнопке
            foreground="#831843", # Цвет текста в кнопке
        )
        style.map("Digit.TButton", background=[("active", "#FCE7F3")]) # Цвет при наведении

        style.configure( # кнопки мат. операций
            "Op.TButton",
            font=("Arial", 14, "bold"),
            padding=8,
            background="#FBCFE8",
            foreground="#831843",
        )
        style.map("Op.TButton", background=[("active", "#F9A8D4")])

        style.configure( # кнопки в правом верхнем углу
            "Action.TButton",
            font=("Arial", 13, "bold"),
            padding=8,
            background="#FECDD3",
            foreground="#9F1239",
        )
        style.map("Action.TButton", background=[("active", "#FDA4AF")])

        style.configure( # кнопка "равно"
            "Equal.TButton",
            font=("Arial", 16, "bold"),
            padding=8,
            background="#EC4899",
            foreground="#FFFFFF",
        )
        style.map("Equal.TButton", background=[("active", "#DB2777")])

    def _build_ui(self):
        # Декоративная шапка с сердечками и цветочками
        top_decor = tk.Label(
            self.root,
            text="✿  ♡  ♥  Калькулятор  ♥  ♡  ✿",
            font=("Arial", 13, "bold"),
            bg="#FFF0F5", 
            fg="#DB2777",
            pady=8, # внутренний отступ по 8 пикселей сверху и снизу, чтобы надпись не прижало
        )
        top_decor.pack(fill="x", pady=(6, 0)) # растягиваем по ширине экрана, создаем внешний отступ : 6 сверху, 0 снизу

        # Поле ввода и поле вывода
        display_frame = tk.Frame(self.root, bg="#FFF0F5", padx=16, pady=6) # по х - 16, по у - 6
        display_frame.pack(fill="x")

        self.expr_var = tk.StringVar() # переменная содержащая поле ввода "12+34"
        self.entry = tk.Entry( # как правильно отобразить
            display_frame, # отображаем в коробочке 2
            textvariable=self.expr_var,  # отображаем актуальный ввод
            font=("Arial", 18),  
            justify="right", # приклеиваем к правой стороне
            bd=2, # толщина рамки
            relief="groove", # тип рамки
            bg="#FFFFFF", # фон
            fg="#831843", # текст
        )
        self.entry.pack(fill="x", pady=(2, 10), ipady=8) # отступ сверху, снизу, толщина рамки
        self.entry.focus_set() # ставим курсор в это окно

        self.result_var = tk.StringVar(value="0") # переменная с ответом
        self.result_label = tk.Label( # поле с ответом
            display_frame,
            textvariable=self.result_var,
            font=("Arial", 16, "bold"),
            bg="#FCE7F3",
            fg="#831843",
            anchor="e",
            padx=12, # отступ по х
            pady=10, # отступ по у
        )
        self.result_label.pack(fill="x")

        # Панель кнопок (5 рядов по 4 кнопки + широкая кнопка "=" внизу)
        buttons_frame = tk.Frame(self.root, bg="#FFF0F5", padx=14, pady=8)
        buttons_frame.pack(fill="both", expand=True)

        layout = [
            [
                ("(", "Op.TButton", lambda: self.insert_char("(")),
                (")", "Op.TButton", lambda: self.insert_char(")")),
                ("C", "Action.TButton", self.clear),
                ("⌫", "Action.TButton", self.backspace),
            ],
            [
                ("7", "Digit.TButton", lambda: self.insert_char("7")),
                ("8", "Digit.TButton", lambda: self.insert_char("8")),
                ("9", "Digit.TButton", lambda: self.insert_char("9")),
                ("/", "Op.TButton", lambda: self.insert_char("/")),
            ],
            [
                ("4", "Digit.TButton", lambda: self.insert_char("4")),
                ("5", "Digit.TButton", lambda: self.insert_char("5")),
                ("6", "Digit.TButton", lambda: self.insert_char("6")),
                ("*", "Op.TButton", lambda: self.insert_char("*")),
            ],
            [
                ("1", "Digit.TButton", lambda: self.insert_char("1")),
                ("2", "Digit.TButton", lambda: self.insert_char("2")),
                ("3", "Digit.TButton", lambda: self.insert_char("3")),
                ("-", "Op.TButton", lambda: self.insert_char("-")),
            ],
            [
                ("0", "Digit.TButton", lambda: self.insert_char("0")),
                (".", "Digit.TButton", lambda: self.insert_char(".")),
                ("√", "Op.TButton", self.calc_sqrt),
                ("+", "Op.TButton", lambda: self.insert_char("+")),
            ],
        ]

        for r, row in enumerate(layout):
            buttons_frame.rowconfigure(r, weight=1) # если окно растягивают, делись свободным местом со строкой r
            for c, (text, style_name, cmd) in enumerate(row): 
                buttons_frame.columnconfigure(c, weight=1)
                btn = ttk.Button(buttons_frame, text=text, style=style_name, command=cmd)
                btn.grid(row=r, column=c, sticky="nsew", padx=4, pady=4)

        # Нижний ряд - широкая кнопка "=" на все 4 столбца
        buttons_frame.rowconfigure(5, weight=1)
        ttk.Button(
            buttons_frame,
            text="=",
            style="Equal.TButton",
            command=self.calculate,
        ).grid(row=5, column=0, columnspan=4, sticky="nsew", padx=4, pady=4)

        # Подсказка в самом низу
        tk.Label(
            self.root,
            text="Enter - посчитать   |   Esc - очистить",
            font=("Arial", 9),
            bg="#FFF0F5",
            fg="#9D174D",
            pady=6,
        ).pack(fill="x", pady=(0, 4))

    def _bind_keyboard(self): # обработка нажатия энтер и эскейп на клавиатуре
        self.root.bind("<KP_Enter>", lambda _event: self.calculate())
        self.root.bind("<Escape>", lambda _event: self.clear())

    def insert_char(self, char: str): # Добавление символов в переменную, содержащую поле ввода
        self.entry.insert(tk.INSERT, char)
        self.entry.focus_set()

    def clear(self): # Очистка всего
        self.expr_var.set("")
        self._show_ok("0")
        self.entry.focus_set()

    def backspace(self): # удаляет последний символ
        current = self.expr_var.get()
        if current:
            self.expr_var.set(current[:-1])
        self.entry.focus_set()

    def _show_ok(self, text: str):
        self.result_label.configure(fg="#831843", bg="#FCE7F3")
        self.result_var.set(text)

    def _show_error(self, text: str):
        self.result_label.configure(fg="#9F1239", bg="#FFE4E6")
        self.result_var.set(f"Ошибка: {text}")

    def calculate(self):
        try:
            value = evaluate_expression(self.expr_var.get())
            self._show_ok(format_number(value))
        except ZeroDivisionError:
            self._show_error("деление на ноль!")
        except ValueError as err:
            self._show_error(str(err))
        except (SyntaxError, TypeError):
            self._show_error("некорректное выражение")
        except OverflowError:
            self._show_error("число слишком велико")

    def calc_sqrt(self):
        try:
            value = evaluate_expression(self.expr_var.get())
            if value < 0:
                raise ValueError("корень из отрицательного числа")
            root_val = math.sqrt(value)
            self._show_ok(format_number(root_val))
        except ZeroDivisionError:
            self._show_error("деление на ноль при вычислении под корнем!")
        except ValueError as err:
            self._show_error(str(err))
        except (SyntaxError, TypeError):
            self._show_error("некорректное выражение")


root = tk.Tk()
CalculatorApp(root)
root.mainloop()