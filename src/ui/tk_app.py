"""Minimal Tkinter chess board for playing against JEV."""

import tkinter as tk
from tkinter import messagebox

import chess

from app.controller import GameController, GameView


PIECE_GLYPHS = {
    "P": "♙", "N": "♘", "B": "♗", "R": "♖", "Q": "♕", "K": "♔",
    "p": "♟", "n": "♞", "b": "♝", "r": "♜", "q": "♛", "k": "♚",
}


class ChessApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Scacchi contro JEV")
        self.root.minsize(560, 620)
        self.canvas = tk.Canvas(root, width=560, height=560, highlightthickness=0)
        self.canvas.pack(padx=12, pady=12)
        self.status_label = tk.Label(root, text="", anchor="w")
        self.status_label.pack(fill="x", padx=12)
        self.error_label = tk.Label(root, text="", fg="#a33", anchor="w")
        self.error_label.pack(fill="x", padx=12)
        controls = tk.Frame(root)
        controls.pack(fill="x", padx=12, pady=10)
        self.retry_button = tk.Button(controls, text="Riprova JEV", command=self.controller_retry)
        self.retry_button.pack(side="left")
        tk.Button(controls, text="Nuova partita", command=self.controller_new_game).pack(side="right")
        self.selected_square: chess.Square | None = None
        self.controller = GameController(self.on_update)
        self.canvas.bind("<Button-1>", self.on_click)
        self.controller.start()

    def on_update(self, view: GameView) -> None:
        self.root.after(0, lambda: self._render(view))

    def _render(self, view: GameView) -> None:
        board = chess.Board(view.fen)
        self.canvas.delete("all")
        square_size = 70
        legal_targets = set()
        if self.selected_square is not None:
            legal_targets = {
                move.to_square for move in board.legal_moves if move.from_square == self.selected_square
            }
        for square in chess.SQUARES:
            file_index = chess.square_file(square)
            rank_index = chess.square_rank(square)
            x = file_index * square_size
            y = (7 - rank_index) * square_size
            color = "#f0d9b5" if (file_index + rank_index) % 2 == 0 else "#b58863"
            if square == self.selected_square:
                color = "#e6c84f"
            elif square in legal_targets:
                color = "#c6d96b"
            self.canvas.create_rectangle(x, y, x + square_size, y + square_size, fill=color, outline=color)
            piece = board.piece_at(square)
            if piece:
                self.canvas.create_text(
                    x + square_size / 2,
                    y + square_size / 2,
                    text=PIECE_GLYPHS[piece.symbol()],
                    font=("Segoe UI Symbol", 42),
                    fill="#222" if piece.color == chess.BLACK else "#fff",
                )
        self.status_label.config(text=view.status + (" | JEV sta pensando..." if view.thinking else ""))
        self.error_label.config(text=view.error or (f"Ultima mossa: {view.last_move_san}" if view.last_move_san else ""))
        self.retry_button.config(state=tk.NORMAL if view.error and not view.thinking else tk.DISABLED)

    def on_click(self, event: tk.Event) -> None:
        view = self.controller.view()
        if view.thinking or view.turn != "white" or self.controller.view().status in {"Scacco matto", "Stallo"}:
            return
        square_size = 70
        file_index = int(event.x // square_size)
        rank_index = 7 - int(event.y // square_size)
        if not (0 <= file_index <= 7 and 0 <= rank_index <= 7):
            return
        square = chess.square(file_index, rank_index)
        board = chess.Board(view.fen)
        if self.selected_square is None:
            piece = board.piece_at(square)
            if piece and piece.color == chess.WHITE:
                self.selected_square = square
        else:
            uci = chess.Move(self.selected_square, square).uci()
            if board.piece_at(self.selected_square).piece_type == chess.PAWN and rank_index in {0, 7}:
                uci += "q"
            if uci in view.legal_moves_uci:
                self.selected_square = None
                self.controller.human_move(uci)
            elif board.piece_at(square) and board.piece_at(square).color == chess.WHITE:
                self.selected_square = square
            else:
                self.selected_square = None
        self._render(self.controller.view())

    def controller_retry(self) -> None:
        self.controller.retry_jev()

    def controller_new_game(self) -> None:
        if messagebox.askyesno("Nuova partita", "Iniziare una nuova partita?"):
            self.selected_square = None
            self.controller.new_game()