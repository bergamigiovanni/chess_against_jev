"""Application entry point."""

import tkinter as tk

from ui.tk_app import ChessApp


def main() -> None:
    root = tk.Tk()
    ChessApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()