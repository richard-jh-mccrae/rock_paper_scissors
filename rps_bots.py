"""Play the Essentially.net rock-paper-scissors game."""

import csv
from dataclasses import dataclass
from enum import Enum
from html.parser import HTMLParser
from http.cookiejar import CookieJar
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.error import URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPCookieProcessor, Request, build_opener


GAME_URL = "https://www.essentially.net/rsp/play.jsp"
_CSV_COLUMNS = ("human_choice", "computer_choice", "result")


class Move(str, Enum):
    ROCK = "rock"
    PAPER = "paper"
    SCISSORS = "scissors"


_WINNING_PAIRS = {
    (Move.ROCK, Move.SCISSORS),
    (Move.PAPER, Move.ROCK),
    (Move.SCISSORS, Move.PAPER),
}


class BotError(RuntimeError):
    """The website could not complete a game round."""


@dataclass(frozen=True)
class RoundResult:
    number: int
    player_move: Move
    computer_move: Move
    outcome: str


def prepare_results_csv(path):
    """Create a results CSV or check its header."""
    path = Path(path)
    if path.exists() and path.stat().st_size:
        with path.open("r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            header = next(reader, None)
            if header == list(_CSV_COLUMNS):
                return path
            if header != ["trial", *_CSV_COLUMNS]:
                raise ValueError("This CSV needs human_choice, computer_choice, result columns.")
            old_rows = list(reader)
        if any(len(row) != 4 for row in old_rows):
            raise ValueError("This CSV needs human_choice, computer_choice, result columns.")
        with NamedTemporaryFile(
            "w", newline="", encoding="utf-8", dir=path.parent, delete=False
        ) as file:
            temporary_path = Path(file.name)
            writer = csv.writer(file)
            writer.writerow(_CSV_COLUMNS)
            writer.writerows(row[1:] for row in old_rows)
        try:
            os.replace(temporary_path, path)
        except OSError:
            temporary_path.unlink(missing_ok=True)
            raise
    else:
        with path.open("a", newline="", encoding="utf-8") as file:
            csv.writer(file).writerow(_CSV_COLUMNS)
    return path


def append_result_csv(path, result: RoundResult):
    """Save one round without a separate trial number."""
    path = prepare_results_csv(path)
    with path.open("a", newline="", encoding="utf-8") as file:
        csv.writer(file).writerow(
            (result.player_move.value, result.computer_move.value, result.outcome)
        )


class _GamePage(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
        self.buttons = {}

    def handle_starttag(self, tag, attrs):
        if tag.lower() not in ("img", "input"):
            return
        attrs = dict(attrs)
        source = attrs.get("src", "")
        name = urlsplit(source).path.rsplit("/", 1)[-1].lower()
        if tag.lower() == "img":
            self.images.append(name)
        elif attrs.get("type", "").lower() == "image":
            self.buttons[name] = attrs.get("name")


def _move_from_button(name):
    return Move.SCISSORS if name == "scissor" else Move(name)


def _read_round(html, expected_move):
    page = _GamePage()
    page.feed(html)

    for index, name in enumerate(page.images):
        if not name.startswith("comp") or name[4:] not in page.buttons:
            continue
        computer_move = _move_from_button(page.buttons[name[4:]])
        player_image = next(
            (item for item in reversed(page.images[:index]) if item in page.buttons), None
        )
        if player_image is None:
            break
        player_move = _move_from_button(page.buttons[player_image])
        if player_move != expected_move:
            raise BotError("The website reported a different player move than the one sent.")
        if player_move == computer_move:
            outcome = "tie"
        elif (player_move, computer_move) in _WINNING_PAIRS:
            outcome = "win"
        else:
            outcome = "loss"
        return computer_move, outcome

    raise BotError("Could not find the computer's move in the website response.")


class EssentiallyBot:
    """Keep one website game session across calls to play()."""

    def __init__(self, timeout=15):
        self.timeout = timeout
        self._opener = None
        self._history = []

    @property
    def history(self):
        return tuple(self._history)

    @property
    def score(self):
        return {
            "wins": sum(row.outcome == "win" for row in self._history),
            "losses": sum(row.outcome == "loss" for row in self._history),
            "ties": sum(row.outcome == "tie" for row in self._history),
        }

    def _get_page(self, opener, data=None):
        headers = {"User-Agent": "ml-lab-101-rps/1.0"}
        if data is not None:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        request = Request(GAME_URL, data=data, headers=headers)
        try:
            with opener.open(request, timeout=self.timeout) as response:
                if response.url != GAME_URL:
                    raise BotError(f"The game redirected to {response.url}.")
                encoding = response.headers.get_content_charset() or "iso-8859-1"
                return response.read().decode(encoding)
        except URLError as error:
            raise BotError(f"Could not reach {GAME_URL}: {error.reason}") from error

    def reset(self):
        """Start a fresh website session and clear the local history."""
        opener = build_opener(HTTPCookieProcessor(CookieJar()))
        html = self._get_page(opener)
        if 'name="rock"' not in html or 'name="paper"' not in html:
            raise BotError("The website did not show the expected game buttons.")
        self._opener = opener
        self._history.clear()
        return self

    def play(self, move: Move):
        """Play one of the Move values."""
        if not isinstance(move, Move):
            raise TypeError("Use Move.ROCK, Move.PAPER, or Move.SCISSORS.")

        if self._opener is None:
            self.reset()
        button = "scissor" if move is Move.SCISSORS else move.value
        data = urlencode({f"{button}.x": 40, f"{button}.y": 40}).encode("ascii")
        html = self._get_page(self._opener, data)
        computer_move, outcome = _read_round(html, move)
        result = RoundResult(len(self._history) + 1, move, computer_move, outcome)
        self._history.append(result)
        return result


bot_1 = EssentiallyBot()
