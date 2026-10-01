"""Coordinate the chess domain, JEV worker and UI callbacks."""

from collections.abc import Callable
from dataclasses import dataclass
from threading import Thread

import chess

from domain.chess_game import ChessGame, PositionSnapshot
from jev_call import jev_choice_request


@dataclass(frozen=True)
class GameView:
    fen: str
    turn: str
    legal_moves_uci: tuple[str, ...]
    status: str
    last_move_san: str | None
    thinking: bool
    error: str | None


class GameController:
    """Keep UI state consistent while JEV requests run in the background."""

    def __init__(
        self,
        on_update: Callable[[GameView], None],
        choice_request: Callable[..., str] = jev_choice_request,
    ) -> None:
        self._game = ChessGame()
        self._on_update = on_update
        self._choice_request = choice_request
        self._version = 0
        self._thinking = False
        self._error: str | None = None
        self._last_move_san: str | None = None

    def view(self) -> GameView:
        snapshot = self._game.snapshot()
        return GameView(
            fen=snapshot.fen,
            turn=snapshot.turn,
            legal_moves_uci=snapshot.legal_moves_uci,
            status=self._game.status,
            last_move_san=self._last_move_san,
            thinking=self._thinking,
            error=self._error,
        )

    def start(self) -> None:
        self._publish()

    def new_game(self) -> None:
        self._version += 1
        self._game.reset()
        self._thinking = False
        self._error = None
        self._last_move_san = None
        self._publish()

    def human_move(self, uci: str) -> None:
        if self._thinking or self._game.is_over or self._game.board.turn != chess.WHITE:
            return
        try:
            self._last_move_san = self._game.apply_uci(uci)
            self._error = None
        except (ValueError, IndexError) as error:
            self._error = str(error)
            self._publish()
            return

        self._publish()
        if not self._game.is_over:
            self._request_jev()

    def retry_jev(self) -> None:
        if not self._thinking and not self._game.is_over and self._game.board.turn == chess.BLACK:
            self._request_jev()

    def _request_jev(self) -> None:
        snapshot = self._game.snapshot()
        version = self._version
        self._thinking = True
        self._error = None
        self._publish()
        Thread(target=self._run_jev, args=(snapshot, version), daemon=True).start()

    def _run_jev(self, snapshot: PositionSnapshot, version: int) -> None:
        try:
            move = self._choice_request(
                question="chess_move",
                state={
                    "fen": snapshot.fen,
                    "turn": snapshot.turn,
                    "legal_moves_uci": list(snapshot.legal_moves_uci),
                    "legal_moves": [
                        {"uci": move, "description": description}
                        for move, description in snapshot.legal_move_descriptions
                    ],
                },
                instructions=(
                    "Choose the best move for black. Return exactly one label from the "
                    "provided chess moves."
                ),
                criteria=dict(snapshot.legal_move_descriptions),
            )
            if move not in snapshot.legal_moves_uci:
                raise ValueError(f"JEV selected an illegal move: {move}")
            if version != self._version:
                return
            self._last_move_san = self._game.apply_uci(move)
            self._thinking = False
            self._error = None
        except Exception as error:
            if version != self._version:
                return
            self._thinking = False
            self._error = str(error)
        self._publish()

    def _publish(self) -> None:
        self._on_update(self.view())