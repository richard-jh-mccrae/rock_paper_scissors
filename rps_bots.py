"""Play the Essentially.net rock-paper-scissors game from a notebook."""

from dataclasses import dataclass
from enum import Enum
from html.parser import HTMLParser
from http.cookiejar import CookieJar
from urllib.error import URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPCookieProcessor, Request, build_opener


GAME_URL = "https://www.essentially.net/rsp/play.jsp"


class Move(str, Enum):
    ROCK = "rock"
    PAPER = "paper"
    SCISSORS = "scissors"


ROCK = Move.ROCK
PAPER = Move.PAPER
SCISSORS = Move.SCISSORS

_MOVES = {
    0: Move.ROCK,
    1: Move.PAPER,
    2: Move.SCISSORS,
    "rock": Move.ROCK,
    "paper": Move.PAPER,
    "scissor": Move.SCISSORS,
    "scissors": Move.SCISSORS,
}
_BUTTON_NAMES = {Move.ROCK: "rock", Move.PAPER: "paper", Move.SCISSORS: "scissor"}
_PLAYER_IMAGES = {"rock.jpg": Move.ROCK, "paper.jpg": Move.PAPER, "scis.jpg": Move.SCISSORS}
_COMPUTER_IMAGES = {
    "comprock.jpg": Move.ROCK,
    "comppaper.jpg": Move.PAPER,
    "compscis.jpg": Move.SCISSORS,
}
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


class _Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.names = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "img":
            return
        source = dict(attrs).get("src", "")
        self.names.append(urlsplit(source).path.rsplit("/", 1)[-1].lower())


def _read_round(html, expected_move):
    images = _Images()
    images.feed(html)

    for index, name in enumerate(images.names):
        if name not in _COMPUTER_IMAGES:
            continue
        earlier = images.names[:index]
        player_image = next((item for item in reversed(earlier) if item in _PLAYER_IMAGES), None)
        if player_image is None:
            break
        player_move = _PLAYER_IMAGES[player_image]
        computer_move = _COMPUTER_IMAGES[name]
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

    def play(self, move):
        """Play a Move, a move name, or 0, 1, 2."""
        if isinstance(move, bool):
            raise ValueError("Use ROCK, PAPER, or SCISSORS.")
        key = move.strip().lower() if isinstance(move, str) else move
        try:
            player_move = _MOVES[key]
        except (KeyError, TypeError):
            raise ValueError("Use ROCK, PAPER, or SCISSORS.") from None

        if self._opener is None:
            self.reset()
        button = _BUTTON_NAMES[player_move]
        data = urlencode({f"{button}.x": 40, f"{button}.y": 40}).encode("ascii")
        html = self._get_page(self._opener, data)
        computer_move, outcome = _read_round(html, player_move)
        result = RoundResult(len(self._history) + 1, player_move, computer_move, outcome)
        self._history.append(result)
        return result


bot_1 = EssentiallyBot()
