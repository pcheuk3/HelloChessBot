# ♟️HelloChessBot

**HelloChessBot** is enhanced version of [NeoChessBot](https://github.com/lamekid123/NeoChessBot). It is designed to help **visually impaired users** play on **Chess.com**. The application integrates **Chess.com** with **voice interaction**, **keyboard navigation**, and **AI-powered assistance**, enabling players to enjoy chess without relying heavily on visual interaction.

## Key Features

- Interface with **speech guidance** for menus, boards, and game states.
- **Keyboard-driven navigation** (tab/enter/space) suitable for screen-reader workflows.
- **Multiple input methods**: command panel (UCI/SAN), arrow-board navigation, and voice input.
- **Voice input** powered by the Whisper model for move commands and UI actions.
- **AI Chat Bot assistant** that answers user questions and performs requests by keywords.
- **Multiple game modes**: support play vs computer, online opponents, and puzzle mode on chess.com.
- **Game review and analysis** with move-by-move feedback and best-move hints.
- **Macro view** to announce vulnerable pieces being attacked.
- **User preference settings** for speech engine on/off, rate, volume, language, and font size.
- **Login persistence** for Chess.com so you don’t need to log in every time.

## Demonstration Video

A demonstration video will be available soon.

## Quick Start (Windows)

1. Download the latest release from:
https://drive.google.com/file/d/1jHpnM4P8rIkgSSxdV7n5__mgH35BYap2/view?usp=sharing (12/3/2026)
2. Unzip the file.
3. Double click `HelloChessBot.exe` to launch.
4. **It is recommended login your chess.com account to enjoy full function**

## User Feedback Survey Form

- https://docs.google.com/forms/d/e/1FAIpQLSfwd12r6qjDhoHnM6fyEnHpjl69Vac_fpbShUTTZHqAG5fXUA/viewform?usp=dialog

## Core Controls (Keyboard)

- **Tab**: move focus through available UI options.
- **Enter / Space**: confirm selection.
- **Ctrl + R**: repeat the last spoken sentence.
- **Ctrl + O**: list available options in the current state.
- **Ctrl + Q**: open the Chat Bot for help and requests.

## Game Modes

- **Play vs Computer**: press the button or `Ctrl + 1`.
- **Play vs Online Player**: press the button or `Ctrl + 2`.
- **Puzzle Mode**: press the button or `Ctrl + 3`.

The bot will announce your side (white/black) once a game starts. In puzzle mode, the starting position and assigned color are announced before the first move.

## Input Methods

### 1) Command Mode (Default)
- Press **Ctrl + F** to focus the command panel.
- Supports **UCI** and **SAN** notation.

**UCI Examples**
- `e2e4`   Move piece from e2 to e4 
- `e7e8q` Pawn moves to e8 and promotes to queen 

**SAN Examples**
- `Nxe4`
- `Rd1+`
- `qe7#`
- `O-O` / `0-0`
- `O-O-O` / `0-0-0`
- `e8=Q`

After input, a confirmation dialog appears. Press **Enter/Space** to confirm, or **Delete** to cancel.

### 2) Arrow Mode (Board Navigation)
- Press **Ctrl + J** to enter arrow mode.
- Use arrow keys to move across squares.
- The bot announces the piece on the current square.
- Press **Space** to select a piece, navigate to the destination, then press **Space** again to drop it.

### 3) Voice Input
- Press **Ctrl + S** to start recording.
- Press **Ctrl + S** again to stop and process the command.

**Recommended move format**: “Move E2 to E4”.

**Voice Keywords / Examples**
- **Select computer mode**: “computer”, “bot”, “pvc”.
- **Select online mode**: “online”, “player”, “pvp”.
- **Select puzzle mode**: “puzzle”.
- **Resign**: “resign”, “surrender”.
- **Time control**: “5+0”, “5 minutes”, “10 plus 5”.
- **Move**: any sentence containing a valid UCI move.

## Chat Bot Assistant

Activate with **Ctrl + Q** or the Chat Bot button. It answers questions and performs actions by keywords such as:

- Greetings: “hi”, “hello”, “nice to meet you”.
- Tutorials: “how to use”, “tutorial”, “help”.
- Input modes: “voice input”, “arrow mode”, “command mode”.
- Shortcuts: “shortcut”, “shortcuts”.
- Options: “what options”, “options”.
- Time control: “5+0”, “10 minutes”, “15 plus 10”.

## In-Game Information & Tools

When in a match, you can navigate the interface to get:

- Remaining time for both sides.
- Piece locations by piece name (e.g. “knight” / “N”).
- Piece type by square name (e.g. “a2”).
- Full piece lists for both sides.
- Move list history.
- **Macro View** to announce vulnerable pieces being attacked.
- press **Current Game Analysis** to analyze current situation. It combines the strength of a professional chess engine with the explanatory ability of a Large Language Model (LLM).
- **Undo Last Move**

## Game End & Review

- The game ends on win or resignation, and the bot announces the result.
- You must resign the current game before starting a new one.
- Press **Resign** button for resign
- Press **A** or use the **Game Review** button after a game finishes.
- In review mode:
  - **Right Arrow**: next move
  - **Left Arrow**: previous move
  - **B**: best move
  - Explanation is shown when available from Chess.com

## Puzzle Mode

- Start with **Ctrl + 3** or the Puzzle Mode button.
- The bot announces assigned color and starting pieces.
- Unlimited time per puzzle (limited number of puzzles for free accounts).
- After solving, you can retry, start a new puzzle, or return home.

## User Preferences

Open the settings menu to adjust:

- Built-in speech engine on/off (screen-reader compatible mode).
- Speech rate and volume.
- Interface font size.
- Language (English / Traditional Chinese / Simplified Chinese).

Settings are stored and restored automatically on launch.

## Voice Input Dependencies

The voice input function relies on the included `ffmpeg` tools and Whisper model file:

- `ffmpeg/` folder (audio processing)
- `small.en.pt` (Whisper model weights)

Keep these files in the same folder as `HelloChessBot.exe` for proper operation.

## FAQ

**Why do I need to grant permission to use this software?**
The bot moves pieces by controlling the mouse cursor, so it requires permission to control input.

**Can I make pre-moves?**
No, pre-moves are not supported in the current version.

**Do I need to log in every time?**
No. Login information is stored and restored automatically.

**Will my settings reset after closing the app?**
No. Preferences are saved and restored on startup.

**How do I remove the software?**
Delete the application folder to remove it.

**How can I report issues or suggestions?**
Contact: pcheuk3-c@my.cityu.edu.hk
