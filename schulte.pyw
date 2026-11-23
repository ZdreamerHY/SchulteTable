import random
import time
import tkinter as tk


BACKGROUND = "#121622"
PANEL = "#1C2334"
TILE = "#273148"
TILE_HOVER = "#354361"
TEXT = "#F4F6FC"
MUTED = "#ACB7CE"
ACCENT = "#B8C7FF"
ACCENT_HOVER = "#D1DAFF"
DARK_TEXT = "#1A2341"
CORRECT = "#203737"
CORRECT_TEXT = "#9EDFCB"
WRONG = "#703845"
WRONG_TEXT = "#FFD6DB"

BODY_FONT = ("Microsoft YaHei UI", 10)
SMALL_FONT = ("Microsoft YaHei UI", 9)
BUTTON_FONT = ("Microsoft YaHei UI", 10, "bold")
NUMBER_FONT = ("Segoe UI", 19, "bold")


class SchulteGame:
    def __init__(self, root):
        self.root = root
        self.size = 5
        self.next_number = 1
        self.mistakes = 0
        self.started_at = None

        self.tiles = {}
        self.size_buttons = {}
        self.clock_job = None
        self.feedback_job = None
        self.feedback_tile = None

        self.target_text = tk.StringVar(root)
        self.time_text = tk.StringVar(root)
        self.mistakes_text = tk.StringVar(root)
        self.status_text = tk.StringVar(root)

        self.build_window()
        self.prepare_round(self.size)

    def make_button(self, parent, text, command, font=BUTTON_FONT):
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=font,
            cursor="hand2",
            relief="flat",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=BACKGROUND,
            highlightcolor=ACCENT,
            background=TILE,
            foreground=TEXT,
            activebackground=TILE_HOVER,
            activeforeground=TEXT,
            disabledforeground=MUTED,
        )

    def build_window(self):
        self.root.title("舒尔特方格")
        self.root.configure(background=BACKGROUND)
        self.root.resizable(False, False)

        content = tk.Frame(self.root, background=BACKGROUND, padx=24, pady=18)
        content.pack()

        tk.Label(
            content,
            text="舒尔特方格",
            font=("Microsoft YaHei UI", 21, "bold"),
            background=BACKGROUND,
            foreground=TEXT,
        ).pack(anchor="w")
        tk.Label(
            content,
            text="按从小到大的顺序点击数字。",
            font=BODY_FONT,
            background=BACKGROUND,
            foreground=MUTED,
        ).pack(anchor="w", pady=(2, 13))

        sizes = tk.Frame(content, background=BACKGROUND)
        sizes.pack(anchor="w", fill="x", pady=(0, 12))
        for size in (4, 5, 6):
            button = self.make_button(
                sizes, f"{size} × {size}", lambda size=size: self.prepare_round(size)
            )
            button.pack(side="left", expand=True, fill="x", padx=2, ipady=3)
            self.size_buttons[size] = button

        stats = tk.Frame(content, background=BACKGROUND)
        stats.pack(fill="x", pady=(0, 10))
        for column, (label, value) in enumerate(
            (("下一个数字", self.target_text), ("用时", self.time_text), ("误点", self.mistakes_text))
        ):
            stats.columnconfigure(column, weight=1, uniform="stat")
            card = tk.Frame(stats, background=PANEL, pady=4)
            card.grid(row=0, column=column, sticky="nsew", padx=2)

            tk.Label(
                card, text=label, font=SMALL_FONT, background=PANEL, foreground=MUTED
            ).pack()
            tk.Label(
                card,
                textvariable=value,
                font=("Segoe UI", 14, "bold"),
                background=PANEL,
                foreground=TEXT,
            ).pack()

        self.board = tk.Frame(content, background=BACKGROUND, width=370, height=370)
        self.board.pack()
        self.board.grid_propagate(False)

        tk.Label(
            content,
            textvariable=self.status_text,
            font=SMALL_FONT,
            background=BACKGROUND,
            foreground=MUTED,
        ).pack(anchor="w", pady=(8, 4))

        self.action_button = self.make_button(content, "开始", self.handle_action)
        self.action_button.configure(
            background=ACCENT,
            foreground=DARK_TEXT,
            activebackground=ACCENT_HOVER,
            activeforeground=DARK_TEXT,
        )
        self.action_button.pack(fill="x", ipady=4)

    def prepare_round(self, size):
        if self.clock_job is not None:
            self.root.after_cancel(self.clock_job)
            self.clock_job = None
        self.clear_feedback()

        self.size = size
        self.next_number = 1
        self.mistakes = 0
        self.started_at = None
        self.target_text.set("—")
        self.time_text.set("0.0 s")
        self.mistakes_text.set("0")
        self.status_text.set("开始后显示数字并计时。")
        self.action_button.configure(text="开始")

        for tile in self.tiles.values():
            tile.destroy()
        self.tiles.clear()

        for index in range(max(self.size_buttons)):
            weight = int(index < size)
            uniform = "tile" if weight else ""
            self.board.rowconfigure(index, weight=weight, uniform=uniform)
            self.board.columnconfigure(index, weight=weight, uniform=uniform)

        numbers = list(range(1, size * size + 1))
        random.shuffle(numbers)
        for index, number in enumerate(numbers):
            row, column = divmod(index, size)
            tile = self.make_button(
                self.board, "·", lambda number=number: self.select_tile(number), NUMBER_FONT
            )
            tile.configure(state="disabled", background=PANEL, highlightthickness=0)
            tile.grid(row=row, column=column, sticky="nsew", padx=3, pady=3)
            self.tiles[number] = tile

        for grid_size, button in self.size_buttons.items():
            selected = grid_size == size
            button.configure(
                background=ACCENT if selected else PANEL,
                foreground=DARK_TEXT if selected else MUTED,
                activebackground=ACCENT_HOVER if selected else TILE_HOVER,
                activeforeground=DARK_TEXT if selected else TEXT,
            )

        self.action_button.focus_set()

    def handle_action(self):
        if self.started_at is not None:
            self.prepare_round(self.size)
        self.start_round()

    def start_round(self):
        for number, tile in self.tiles.items():
            tile.configure(text=str(number), state="normal", background=TILE)

        self.target_text.set("1")
        self.status_text.set("按顺序点击，点错会计入误点。")
        self.action_button.configure(text="重开")
        self.started_at = time.perf_counter()
        self.update_clock()
        next(iter(self.tiles.values())).focus_set()

    def update_clock(self):
        self.show_elapsed()
        self.clock_job = self.root.after(50, self.update_clock)

    def show_elapsed(self):
        elapsed = time.perf_counter() - self.started_at
        self.time_text.set(f"{elapsed:.1f} s")

    def clear_feedback(self):
        if self.feedback_job is not None:
            self.root.after_cancel(self.feedback_job)
            self.feedback_job = None

        if self.feedback_tile is not None:
            self.feedback_tile.configure(
                background=TILE, activebackground=TILE_HOVER, activeforeground=TEXT
            )
            self.feedback_tile = None

    def select_tile(self, number):
        tile = self.tiles[number]
        if self.started_at is None or str(tile["state"]) != "normal":
            return

        self.clear_feedback()
        if number != self.next_number:
            self.mistakes += 1
            self.mistakes_text.set(str(self.mistakes))
            tile.configure(background=WRONG, activebackground=WRONG, activeforeground=WRONG_TEXT)
            self.feedback_tile = tile
            self.feedback_job = self.root.after(250, self.clear_feedback)
            return

        tile.configure(
            state="disabled", background=CORRECT, disabledforeground=CORRECT_TEXT
        )
        self.next_number += 1

        if self.next_number > self.size * self.size:
            self.finish_round()
        else:
            self.target_text.set(str(self.next_number))

    def finish_round(self):
        self.show_elapsed()
        self.root.after_cancel(self.clock_job)
        self.clock_job = None

        self.target_text.set("—")
        self.status_text.set("完成！再来一局会换一套排列。")
        self.action_button.configure(text="再来一局")
        self.action_button.focus_set()


if __name__ == "__main__":
    root = tk.Tk()
    SchulteGame(root)
    root.mainloop()
