# ♛ Murder at the Black Castle

A two-player chessboard detective game built with Python and Streamlit. The Black King has been murdered, and six suspects have each made three moves since the crime. Play as the White Queen or Black Queen, question suspects, and reconstruct their movements to uncover the killer.

Both detectives see the same evidence. The first player to make a correct accusation wins; a wrong accusation hands victory to the other player.

## Features

- Randomly generated mysteries with six suspects and three hidden moves per suspect.
- Turn-based play for two people sharing one browser session.
- Queen movement with a limited budget of points each round.
- A shared evidence table that reveals each suspect's history one move at a time.
- An SVG investigation board and a separate board showing the latest reconstructed move.
- An investigation log and a complete solution revealed when the game ends.

## Getting started

### Requirements

- Python 3.10 or newer.
- [uv](https://docs.astral.sh/uv/) installed and available in your terminal.

### Run with uv

From the project directory:

```bash
uv sync
uv run streamlit run app.py
```

Open the local URL printed by Streamlit in your browser. Stop the server with `Ctrl+C`.

`uv sync` creates a `.venv` environment and installs the project's dependencies using `pyproject.toml` and `uv.lock`. There is no need to activate the environment when using `uv run`.

To activate it manually on macOS or Linux:

```bash
source .venv/bin/activate
streamlit run app.py
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
streamlit run app.py
```

Run `deactivate` when you want to leave the environment.

### Run with pip

If you prefer pip, create and activate a virtual environment, then run:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## How to play

### The mystery

The red **✕** marks the murder square. The suspects are the Black and White Knights, Bishops, and Rooks. Each has a hidden history of three moves; the murderer was on the murder square at the time of the crime.

White Queen takes the first turn. Players alternate turns in the same browser session.

### Your turn

Choose one action:

| Action | What happens |
| --- | --- |
| **Interrogate** | Choose a suspect and an available adjacent square. Your queen moves there, spends movement points, and reveals one earlier position of that suspect. |
| **Skip turn** | Pass to the other detective while keeping your remaining movement points. |
| **End my movement round** | Forfeit your remaining points and wait for the other detective to finish the round. |
| **Accuse** | Name the killer. A correct accusation wins immediately; an incorrect accusation gives the other detective the win. |

### Movement and rounds

- Each queen starts with **15 movement points**.
- Queens move horizontally, vertically, or diagonally in a straight line. Each traversed square costs one point.
- Queens cannot move through or land on occupied squares.
- An interrogation requires a square next to the suspect, including diagonally adjacent squares. If your queen is already adjacent, you can question that suspect without spending movement points.
- Each interrogation reveals one move and ends your turn. A suspect can be questioned up to three times.
- A queen who runs out of points or ends the round early waits, passing any waiting turns.
- Once both queens have finished their movement round, both receive **15 fresh points**. Unused points do not carry over.

### Reading the evidence

Interrogations rewind a suspect's position on the board. Each suspect stays at the most recently revealed position.

| Clue | Position revealed |
| --- | --- |
| First interrogation | One move before the starting investigation position |
| Second interrogation | Two moves before the starting investigation position |
| Third interrogation | The suspect's position at the time of the murder |

Both players share every revealed clue. Use the evidence table to compare histories and the latest reconstructed movement board to follow the most recent reveal.

The murderer is the suspect whose position at the time of the murder matches the red **✕**. The murder marker is evidence rather than an occupying chess piece.

Use **Generate new mystery** in the sidebar to reset the game at any time, or **Play another case** after a winner is declared.

## Project structure

```text
.
├── app.py             # Streamlit entry point
├── ui.py              # Interface, player actions, and session-state interactions
├── game.py            # Movement rules, case generation, and game-state helpers
├── board.py           # HTML and SVG board rendering
├── constants.py       # Board labels, suspects, queens, and piece glyphs
├── pyproject.toml     # Project metadata and uv dependency configuration
├── uv.lock            # Locked dependency versions for uv
├── requirements.txt   # Dependency specification for pip
└── README.md
```

Game logic lives in `game.py`; presentation lives in `ui.py` and `board.py`. Keep `app.py` as the entry point when starting Streamlit. If you change dependencies, keep `pyproject.toml` and `requirements.txt` aligned and update `uv.lock` with `uv lock`.

## Game sessions

Progress is held in Streamlit session state, with no database or saved-game files. Treat it as temporary: restarting the server or losing the browser session can start a new case. Two players should share a single session to play against each other.

For fair play, use the clues shown in the interface rather than inspecting the underlying game state. The full solution becomes visible after an accusation ends the game.
