"""Run with python rps_gui.py to play the online bot and save each round."""

from pathlib import Path
from queue import Empty, Queue
from threading import Event, Thread
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import webbrowser

from PIL import Image, ImageOps, ImageTk

from rps_bots import EssentiallyBot, GAME_URL, Move, append_result_csv, prepare_results_csv


IMAGE_FILES = {
    Move.ROCK: "rock.jpg",
    Move.PAPER: "paper.jpg",
    Move.SCISSORS: "scis.jpg",
}


class RpsApp:
    def __init__(self, root):
        self.root = root
        self.bot = EssentiallyBot()
        self.bot_ready = Event()
        self.replies = Queue()
        self.busy = False
        self.pending = None
        self.file_path = tk.StringVar()
        self.result_text = tk.StringVar(value="Choose a CSV file, then pick a move.")
        self.score_text = tk.StringVar(value="Wins: 0    Losses: 0    Ties: 0")
        self.move_images = {}
        for move, filename in IMAGE_FILES.items():
            with Image.open(Path(__file__).parent / "images" / filename) as picture:
                fitted = ImageOps.contain(picture.convert("RGB"), (165, 110))
                self.move_images[move] = ImageTk.PhotoImage(fitted, master=root)

        root.title("Rock Paper Scissors")
        root.geometry("790x650")
        root.minsize(720, 620)
        root.configure(background="#f3f6fa")
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TFrame", background="#f3f6fa")
        style.configure("TLabel", background="#f3f6fa", foreground="#1c3044", font=("Segoe UI", 14))
        style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"))
        style.configure("Section.TLabel", font=("Segoe UI", 14, "bold"))
        style.configure("Link.TLabel", foreground="#1769aa", font=("Segoe UI", 14, "underline"))
        style.configure(
            "TButton", background="white", foreground="#1c3044", font=("Segoe UI", 14), padding=(12, 8)
        )
        style.configure("Move.TButton", font=("Segoe UI", 14, "bold"), padding=(12, 10))
        style.map("TButton", background=[("active", "#e5effa")])

        frame = ttk.Frame(root, padding=20)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text="Rock · Paper · Scissors", style="Title.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 10)
        )
        ttk.Label(frame, text="Results CSV", style="Section.TLabel").grid(
            row=1, column=0, sticky="w"
        )
        ttk.Entry(frame, textvariable=self.file_path, font=("Segoe UI", 14)).grid(
            row=2, column=0, columnspan=3, sticky="ew", pady=(4, 6), ipady=5
        )
        ttk.Button(frame, text="Use existing…", command=self.choose_existing).grid(
            row=3, column=0, sticky="w"
        )
        ttk.Button(frame, text="Create new…", command=self.choose_new).grid(
            row=3, column=1, sticky="w", padx=8
        )

        ttk.Separator(frame).grid(row=4, column=0, columnspan=3, sticky="ew", pady=10)
        ttk.Label(frame, text="Choose your move", style="Section.TLabel").grid(
            row=5, column=0, columnspan=3, sticky="w", pady=(0, 6)
        )
        moves = ttk.Frame(frame)
        moves.grid(row=6, column=0, columnspan=3, sticky="ew")
        self.move_buttons = []
        for column, move in enumerate((Move.ROCK, Move.PAPER, Move.SCISSORS)):
            moves.columnconfigure(column, weight=1)
            button = ttk.Button(
                moves,
                text=move.value.title(),
                image=self.move_images[move],
                compound="top",
                style="Move.TButton",
                command=lambda m=move: self.play(m),
            )
            button.grid(row=0, column=column, sticky="ew", padx=(0, 10) if column < 2 else 0)
            self.move_buttons.append(button)

        result = ttk.Frame(frame)
        result.grid(row=7, column=0, columnspan=3, sticky="ew", pady=(16, 0))
        image_space = ttk.Frame(result, width=165, height=110)
        image_space.grid(row=0, column=0, rowspan=2, padx=(0, 18))
        image_space.grid_propagate(False)
        self.computer_image = ttk.Label(image_space)
        self.computer_image.place(relx=0.5, rely=0.5, anchor="center")
        ttk.Label(result, textvariable=self.result_text, wraplength=470).grid(
            row=0, column=1, sticky="sw", pady=(0, 8)
        )
        ttk.Label(result, textvariable=self.score_text).grid(
            row=1, column=1, sticky="nw"
        )
        footer = ttk.Frame(frame)
        footer.grid(row=8, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        self.save_button = ttk.Button(footer, text="Save unsaved round", command=self.save_pending)
        self.save_button.pack(side="left")
        self.save_button.state(["disabled"])
        credit = ttk.Label(
            footer,
            text="Online bot and hand images: Essentially.net",
            style="Link.TLabel",
            cursor="hand2",
        )
        credit.pack(side="right")
        credit.bind("<Button-1>", lambda event: webbrowser.open(GAME_URL))
        Thread(target=self.prepare_bot, daemon=True).start()

    def prepare_bot(self):
        try:
            self.bot.reset()
        except Exception:
            pass
        finally:
            self.bot_ready.set()

    def choose_existing(self):
        path = filedialog.askopenfilename(
            parent=self.root, title="Choose results CSV", filetypes=[("CSV files", "*.csv")]
        )
        if path:
            self.file_path.set(path)

    def choose_new(self):
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Create results CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
        )
        if path:
            self.file_path.set(path)

    def selected_path(self):
        name = self.file_path.get().strip()
        if not name:
            raise ValueError("Choose or enter a CSV file first.")
        path = Path(name).expanduser()
        if path.suffix.lower() != ".csv":
            raise ValueError("The results file must end in .csv.")
        return path

    def play(self, move):
        if self.busy or self.pending is not None:
            return
        try:
            path = self.selected_path()
            prepare_results_csv(path)
        except (OSError, ValueError) as error:
            messagebox.showerror("Results CSV", str(error), parent=self.root)
            return

        self.busy = True
        for button in self.move_buttons:
            button.state(["disabled"])
        self.result_text.set("Waiting for the online bot…")
        Thread(target=self.play_online, args=(move, path), daemon=True).start()
        self.root.after(20, self.check_reply)

    def play_online(self, move, path):
        try:
            self.bot_ready.wait()
            self.replies.put((path, self.bot.play(move), None))
        except Exception as error:
            self.replies.put((path, None, error))

    def check_reply(self):
        try:
            path, result, error = self.replies.get_nowait()
        except Empty:
            self.root.after(20, self.check_reply)
            return

        self.busy = False
        if error is not None:
            self.result_text.set("The online game did not finish this round.")
            messagebox.showerror("Online bot", str(error), parent=self.root)
        else:
            self.pending = result
            self.show_result(result)
            self.save_pending(path)
        self.update_buttons()

    def show_result(self, result):
        self.computer_image.configure(image=self.move_images[result.computer_move])
        self.result_text.set(
            f"Computer chose {result.computer_move.value.title()}. "
            f"{result.outcome.title()}."
        )
        score = self.bot.score
        self.score_text.set(
            f"Wins: {score['wins']}    Losses: {score['losses']}    Ties: {score['ties']}"
        )

    def save_pending(self, path=None):
        if self.pending is None:
            return
        try:
            path = path or self.selected_path()
            append_result_csv(path, self.pending)
        except (OSError, ValueError) as error:
            self.result_text.set(self.result_text.get() + " Round not saved yet.")
            messagebox.showerror("Could not save round", str(error), parent=self.root)
        else:
            self.pending = None
            self.result_text.set(self.result_text.get() + " Saved to CSV.")
        self.update_buttons()

    def update_buttons(self):
        if not self.busy and self.pending is None:
            for button in self.move_buttons:
                button.state(["!disabled"])
        self.save_button.state(["!disabled"] if self.pending is not None else ["disabled"])


def main():
    root = tk.Tk()
    RpsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
