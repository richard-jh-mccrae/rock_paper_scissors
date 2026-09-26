# Rock Paper Scissors

## Python API

```python
from rps_bots import EssentiallyBot, Move

bot = EssentiallyBot()
result = bot.play(Move.ROCK)
print(result.player_move.value, result.computer_move.value, result.outcome)
print(bot.score)
```

Use `Move.ROCK`, `Move.PAPER`, or `Move.SCISSORS`. Each call to `play` keeps the
same online game session. `result.number` gives the round number, and
`bot.reset()` starts a new game.

## GUI

# Dependency
Install via:

```bash
python -m pip install -r requirements.txt
```

Run `python rps_gui.py`. Choose or create a results CSV, then click a move.
The GUI shows the computer's move and saves each round to the CSV.

## Test

Run the random-play test with `python -m unittest discover -s tests -v`.
It plays ten live rounds against Essentially.net, so it needs an internet connection.

## Credits

The online bot is provided by [Essentially.net's Rock-Paper-Scissors game](https://www.essentially.net/rsp/play.jsp).
The hand images in `images/` come from that same game page.
