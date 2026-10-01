"""Rule-aware chess game state, independent from the user interface."""

from dataclasses import dataclass

import chess


@dataclass(frozen=True)
class PositionSnapshot:
    fen: str
    turn: str
    legal_moves_uci: tuple[str, ...]
    legal_move_descriptions: tuple[tuple[str, str], ...]


class ChessGame:
    """Owns the board and applies only legal moves."""

    def __init__(self) -> None:
        self.board = chess.Board()

    def reset(self) -> None:
        self.board.reset()

    @property
    def is_over(self) -> bool:
        return self.board.is_game_over()

    @property
    def status(self) -> str:
        if self.board.is_checkmate():
            return "Scacco matto"
        if self.board.is_stalemate():
            return "Stallo"
        if self.board.is_insufficient_material():
            return "Patta: materiale insufficiente"
        if self.board.is_check():
            return "Scacco"
        return "Turno del bianco" if self.board.turn == chess.WHITE else "Turno del nero"

    def legal_moves(self) -> tuple[chess.Move, ...]:
        return tuple(self.board.legal_moves)

    def snapshot(self) -> PositionSnapshot:
        legal_moves = tuple(self.board.legal_moves)
        legal_move_descriptions = tuple(
            (move.uci(), self._describe_move(move)) for move in legal_moves
        )

        return PositionSnapshot(
            fen=self.board.fen(),
            turn="white" if self.board.turn == chess.WHITE else "black",
            legal_moves_uci=tuple(move.uci() for move in legal_moves),
            legal_move_descriptions=legal_move_descriptions,
        )

    def _describe_move(self, move: chess.Move) -> str:
        piece = self.board.piece_at(move.from_square)
        if piece is None:
            raise ValueError(f"No piece on source square: {move.uci()}")
        color = "white" if piece.color == chess.WHITE else "black"
        piece_name = chess.piece_name(piece.piece_type)
        action = "captures on" if self.board.is_capture(move) else "moves to"
        description = f"{color} {piece_name} from {chess.square_name(move.from_square)} {action} {chess.square_name(move.to_square)}"
        if move.promotion:
            description += f" and promotes to {chess.piece_name(move.promotion)}"
        return description

    def apply_uci(self, uci: str) -> str:
        move = chess.Move.from_uci(uci)
        if move not in self.board.legal_moves:
            raise ValueError(f"Mossa illegale: {uci}")
        san = self.board.san(move)
        self.board.push(move)
        return san