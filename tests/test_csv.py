"""Check the CSV file used by the API and GUI."""

import csv
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from rps_bots import Move, RoundResult, append_result_csv, prepare_results_csv


class ResultsCsvTest(unittest.TestCase):
    def test_new_csv_has_no_trial_column(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "results.csv"
            prepare_results_csv(path)
            append_result_csv(path, RoundResult(1, Move.ROCK, Move.SCISSORS, "win"))

            with path.open(newline="", encoding="utf-8") as file:
                rows = list(csv.reader(file))
            self.assertEqual(
                rows,
                [
                    ["human_choice", "computer_choice", "result"],
                    ["rock", "scissors", "win"],
                ],
            )

    def test_old_csv_keeps_its_rounds_when_trial_column_is_removed(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "results.csv"
            path.write_text(
                "trial,human_choice,computer_choice,result\n"
                "1,rock,scissors,win\n",
                encoding="utf-8",
            )
            append_result_csv(path, RoundResult(2, Move.PAPER, Move.ROCK, "win"))

            with path.open(newline="", encoding="utf-8") as file:
                rows = list(csv.reader(file))
            self.assertEqual(
                rows,
                [
                    ["human_choice", "computer_choice", "result"],
                    ["rock", "scissors", "win"],
                    ["paper", "rock", "win"],
                ],
            )


if __name__ == "__main__":
    unittest.main()
