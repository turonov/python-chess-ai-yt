
# AI Chess with Stockfish

This project integrates Stockfish into a Python-based chess engine. It allows players to:
- Analyze board positions using Stockfish.
- Get the best suggested moves.
- Save game history in PGN format.
- Play with an AI opponent at a configurable Elo level.

## Installation

1. Install dependencies:
   ```bash
   pip install pygame python-chess
   ```

2. Download and install Stockfish:
   - [Stockfish Official Site](https://stockfishchess.org/download/)

3. Update `stockfish_config.py` with the correct path to the Stockfish binary.

## Usage

To start the game, run:
```bash
python src/main.py
```

## Features

- **Stockfish Analysis**: Provides real-time analysis and move suggestions.
- **PGN Save**: Stores game history in PGN format.
- **Configurable Strength**: Adjust the AI's Elo rating for different skill levels.

## License

This project is open-source and free to use.
