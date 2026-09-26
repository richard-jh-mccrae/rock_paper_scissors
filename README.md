# Rock Paper Scissors

## Python API

```python
from rps_bots import EssentiallyBot, Move, append_result_csv

bot = EssentiallyBot()
result = bot.play(Move.ROCK)
print(result.player_move.value, result.computer_move.value, result.outcome)
print(bot.score)
append_result_csv("results.csv", result)
```

Pass `Move.ROCK`, `Move.PAPER`, or `Move.SCISSORS` to `play`; strings and numbers
are not accepted. Each call to `play` keeps the same online game session. WARNING
for large number of games, website query requires 0.6s per game.
`result.number` gives the round number, and
`bot.reset()` starts a new game.

The CSV has `human_choice`, `computer_choice`, and `result` columns. Its row
order gives the trial number. Existing CSVs with a `trial` column are converted
when opened.

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
