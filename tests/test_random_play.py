"""Play ten random rounds against the online bot."""

import random
import unittest

from rps_bots import EssentiallyBot, Move


MOVES = tuple(Move)
BEATS = {Move.ROCK: Move.SCISSORS, Move.PAPER: Move.ROCK, Move.SCISSORS: Move.PAPER}


class RandomPlayTest(unittest.TestCase):
    def test_random_moves_play_ten_online_rounds(self):
        bot = EssentiallyBot()

        for trial in range(1, 11):
            move = random.choice(MOVES)
            round_result = bot.play(move)
            with self.subTest(trial=trial):
                human = round_result.player_move
                computer = round_result.computer_move
                self.assertEqual(round_result.number, trial)
                self.assertIs(human, move)
                self.assertIn(computer, MOVES)
                expected = "tie" if human == computer else "win" if BEATS[human] == computer else "loss"
                self.assertEqual(round_result.outcome, expected)
            print(f"{trial}: {human.value} vs {computer.value} -> {round_result.outcome}", flush=True)

        self.assertEqual(len(bot.history), 10)
        self.assertEqual(sum(bot.score.values()), 10)


if __name__ == "__main__":
    unittest.main()
