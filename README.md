# Chess against JEV

Desktop chess game: the human player controls white, while JEV chooses black's
moves. `python-chess` is the source of truth for all chess rules; JEV never gets
to apply an unchecked move directly.

## Setup

From PowerShell, in the project directory:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Create `.env` with an API key:

```env
TYPESAFE_API_KEY=your_key_here
```

`.env` is ignored by Git and must never be committed.

## Run

```powershell
.\venv\Scripts\python.exe src\main.py
```

Click a white piece and then one of its highlighted legal destination squares.
After the move, JEV receives the current FEN, the side to move, the SAN move
history, and every legal move in UCI notation. JEV must return one of those UCI
labels. The local chess board validates the result before applying it.

If the request fails or JEV returns an invalid choice, the board is unchanged
and the **Riprova JEV** button can be used to retry.

## Current scope

- Standard initial position.
- Human plays white; JEV plays black.
- Legal move validation, castling, promotion, en passant, check and game-over
	detection come from `python-chess`.
- The JEV request runs in a worker thread so the Tkinter window remains usable.
- No real API calls are made by the offline controller smoke test.