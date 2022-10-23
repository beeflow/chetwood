import sys
import unittest
from io import StringIO

from unittest_data_provider import data_provider

from connectz import ConnectZ, ConnectZException, GameOutput, GameOutputReason, get_filename, main


class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio  # free up some memory
        sys.stdout = self._stdout


class TestConnectZ(unittest.TestCase):
    incorrect_games_specifications = lambda: (  # noqa
        ("1 1",),
        ("1 1 ",),
        ("3 2 1 4",),
        ("a 2 3 4",),
        (" 2 3",),
        ("1  2 3",),
    )

    correct_games_specifications = lambda: (  # noqa
        ("3 2 1",),
        ("6 7 4",),
    )

    illegal_game_specifications = lambda: (  # noqa
        ("1 2 3",),
        ("2 4 6",),
        ("7 6 8",),
    )

    incorrect_script_aruments = lambda: (  # noqa
        (("arg1", "arg2", "arg3"),),
        (("arg1",),),
    )

    def setUp(self) -> None:
        self.game_test = ConnectZ()

    def test_open_file_failed_no_filename(self):
        """Should fail because of missing filename attribute."""
        with self.assertRaises(ConnectZException):
            self.game_test.open_file()

    def test_open_file_failed_no_file(self):
        """Should fail because file doesn't exist."""
        self.game_test.filename = "some_filename.txt"

        try:
            self.game_test.open_file()
            self.assertTrue(False)
        except ConnectZException as exc:
            self.assertEqual(exc.code, GameOutput.FILE_ERROR.value)
            self.assertEqual(exc.message, GameOutputReason.FILE_ERROR.value)

    @data_provider(incorrect_games_specifications)
    def test_set_game_specification_failed_missing_data(self, incorrect_specification):
        try:
            self.game_test.set_game_specification(incorrect_specification)
            self.assertTrue(False)
        except ConnectZException as exc:
            self.assertEqual(exc.code, GameOutput.INVALID_FILE.value)

    @data_provider(correct_games_specifications)
    def test_set_game_specification_success(self, correct_specification):
        columns, rows, counters = correct_specification.split(" ")
        self.game_test.set_game_specification(correct_specification)

        self.assertEqual(int(columns), self.game_test.columns)
        self.assertEqual(int(rows), self.game_test.rows)
        self.assertEqual(int(counters), self.game_test.counters)

    @data_provider(illegal_game_specifications)
    def test_illegal_game(self, illegal_game):
        try:
            self.game_test.set_game_specification(illegal_game)
            self.assertTrue(False)
        except ConnectZException as exc:
            self.assertEqual(exc.code, GameOutput.ILLEGAL_GAME.value)

    def test_player_1_number(self):
        for line_number in range(0, 10, 2):
            self.assertEqual(1, self.game_test.get_player_number(line_number))

    def test_player_2_number(self):
        for line_number in range(1, 10, 2):
            self.assertEqual(2, self.game_test.get_player_number(line_number))

    def test_add_to_column_failed_column_too_high(self):
        columns = 4
        self.game_test.taken_lines_in_column = [-1 for _ in range(columns)]

        try:
            self.game_test.add_to_column(1, 5)
            self.assertTrue(False)
        except ConnectZException as exc:
            self.assertEqual(exc.code, GameOutput.INVALID_FILE.value)

    def test_add_to_column_failed_negative_column_number(self):
        columns = 4
        self.game_test.taken_lines_in_column = [-1 for _ in range(columns)]

        try:
            self.game_test.add_to_column(1, -1)
            self.assertTrue(False)
        except ConnectZException as exc:
            self.assertEqual(exc.code, GameOutput.INVALID_FILE.value)

    # noinspection Duplicates
    def test_add_to_column_success(self):
        elements = (1, 2, 1, 2, 1, 2, 1)
        self.game_test.columns = 7
        self.game_test.rows = 6
        self.game_test.counters = 4

        self.game_test.prepare_game_board()

        self.game_test.taken_lines_in_column = [-1 for _ in range(self.game_test.columns)]

        for line_number, selected_column in enumerate(elements):
            player = self.game_test.get_player_number(line_number)
            self.game_test.add_to_column(player, selected_column)

        expected_result = [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [1, 0, 0, 0, 0, 0, 0],
            [1, 2, 0, 0, 0, 0, 0],
            [1, 2, 0, 0, 0, 0, 0],
            [1, 2, 0, 0, 0, 0, 0],
        ]

        self.assertEqual(expected_result, self.game_test.game_board[::-1])
        self.assertTrue(self.game_test.is_winner(1))

    # noinspection Duplicates
    def test_add_to_row_success(self):
        elements = (1, 1, 2, 2, 3, 3, 4)

        self.game_test.columns = 7
        self.game_test.rows = 6
        self.game_test.counters = 4

        self.game_test.prepare_game_board()

        self.game_test.taken_lines_in_column = [-1 for _ in range(self.game_test.columns)]

        for line_number, selected_column in enumerate(elements):
            player = self.game_test.get_player_number(line_number)
            self.game_test.add_to_column(player, selected_column)

        expected_result = [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [2, 2, 2, 0, 0, 0, 0],
            [1, 1, 1, 1, 0, 0, 0],
        ]

        self.assertEqual(expected_result, self.game_test.game_board[::-1])
        self.assertTrue(self.game_test.is_winner(1))

    # noinspection Duplicates
    def test_add_to_diagonal_success(self):
        elements = (1, 2, 2, 3, 3, 4, 4, 4, 4, 2, 3)

        self.game_test.columns = 7
        self.game_test.rows = 6
        self.game_test.counters = 4

        self.game_test.prepare_game_board()

        self.game_test.taken_lines_in_column = [-1 for _ in range(self.game_test.columns)]

        for line_number, selected_column in enumerate(elements):
            player = self.game_test.get_player_number(line_number)
            self.game_test.add_to_column(player, selected_column)

        expected_result = [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0],
            [0, 2, 1, 2, 0, 0, 0],
            [0, 1, 1, 1, 0, 0, 0],
            [1, 2, 2, 2, 0, 0, 0],
        ]

        self.assertEqual(expected_result, self.game_test.game_board[::-1])
        self.assertTrue(self.game_test.is_winner(1))

    def test_add_to_row_too_many_in_row(self):
        elements = (1, 1, 1, 1, 1, 1, 1)

        self.game_test.columns = 7
        self.game_test.rows = 6
        self.game_test.counters = 4

        self.game_test.prepare_game_board()

        self.game_test.taken_lines_in_column = [-1 for _ in range(self.game_test.columns)]

        with self.assertRaises(ConnectZException):
            for line_number, selected_column in enumerate(elements):
                player = self.game_test.get_player_number(line_number)
                self.game_test.add_to_column(player, selected_column)

    def test_p1_wins(self):
        result = self.game_test.test_game("tests/fixtures/p1_wins.txt")

        self.assertEqual(GameOutput.WIN_FOR_PLAYER_1, GameOutput(result))

    def test_impossible_game(self):
        try:
            self.game_test.test_game("tests/fixtures/impossible_game.txt")
            self.assertTrue(False)
        except ConnectZException as exc:
            self.assertEqual(GameOutput.ILLEGAL_GAME, GameOutput(exc.code))

    def test_no_wins(self):
        result = self.game_test.test_game("tests/fixtures/no_wins.txt")

        self.assertEqual(GameOutput.INCOMPLETE, GameOutput(result))

    def test_illegal_continue(self):
        try:
            self.game_test.test_game("tests/fixtures/illegal_continue.txt")
            self.assertTrue(False)
        except ConnectZException as exc:
            self.assertEqual(GameOutput.ILLEGAL_CONTINUE, GameOutput(exc.code))

    def test_invalid_file(self):
        try:
            self.game_test.test_game("tests/fixtures/invalid_file.txt")
            self.assertTrue(False)
        except ConnectZException as exc:
            self.assertEqual(GameOutput.INVALID_FILE, GameOutput(exc.code))

    def test_no_empty_space(self):
        result = self.game_test.test_game("tests/fixtures/no_empty_space.txt")
        self.assertEqual(GameOutput.DRAW, GameOutput(result))

    def test_p1_wins_diagonally_right(self):
        result = self.game_test.test_game("tests/fixtures/p1_wins_dr.txt")
        self.assertEqual(GameOutput.WIN_FOR_PLAYER_1, GameOutput(result))

    def test_get_filename_success(self):
        filename = "some_file_name.txt"

        self.assertEqual(filename, get_filename(("", filename)))

    @data_provider(incorrect_script_aruments)
    def test_get_filename_failed(self, incorrect_arguments):
        with Capturing() as output:
            with self.assertRaises(SystemExit):
                get_filename(incorrect_arguments)

    def test_main_success(self):
        with Capturing() as output:
            argv = ("", "tests/fixtures/p1_wins.txt")
            main(argv)

        self.assertEqual([str(GameOutput.WIN_FOR_PLAYER_1.value)], output)

    def test_main_failed(self):
        with Capturing() as output:
            argv = ("", "tests/fixtures/empty_file.txt")
            main(argv)

        self.assertEqual([str(GameOutput.INVALID_FILE.value)], output)
