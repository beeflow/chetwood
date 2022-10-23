import sys
from enum import Enum, auto
from io import StringIO


class GameOutput(Enum):
    DRAW = 0
    WIN_FOR_PLAYER_1 = auto()
    WIN_FOR_PLAYER_2 = auto()
    INCOMPLETE = auto()
    ILLEGAL_CONTINUE = auto()
    ILLEGAL_ROW = auto()
    ILLEGAL_COLUMN = auto()
    ILLEGAL_GAME = auto()
    INVALID_FILE = auto()
    FILE_ERROR = auto()


class GameOutputReason(Enum):
    DRAW = "Draw"
    WIN_FOR_PLAYER_1 = "Win for player 1"
    WIN_FOR_PLAYER_2 = "Win for player 2"
    INCOMPLETE = "Incomplete"
    ILLEGAL_CONTINUE = "Illegal continue"
    ILLEGAL_ROW = "Illegal row"
    ILLEGAL_COLUMN = "Illegal column"
    ILLEGAL_GAME = "Illegal game"
    INVALID_FILE = "Invalid file"
    FILE_ERROR = "File error"


class ConnectZException(BaseException):
    def __init__(self, *args, code: int, message: str):
        self.code = code
        self.message = message

        super().__init__(*args)


class ConnectZ:
    filename: str
    file: StringIO = None

    columns: int
    rows: int
    counters: int

    is_won: bool = False
    winner: GameOutput

    game_board: list
    taken_lines_in_column: list

    possible_winners_result: tuple = (
        GameOutput.WIN_FOR_PLAYER_1,
        GameOutput.WIN_FOR_PLAYER_2,
    )

    def __init__(self):
        self.game_board = []

    def test_game(self, filename):
        self.filename = filename

        self.open_file()
        self.set_game_specification(self.file.readline())
        self.prepare_game_board()

        line_number = 0

        while True:
            line = self.file.readline()

            if not line:
                break

            if self.is_won:
                raise ConnectZException(
                    code=GameOutput.ILLEGAL_CONTINUE.value, message=GameOutputReason.ILLEGAL_CONTINUE.value
                )
            try:
                selected_column = int(line)
            except ValueError:
                raise ConnectZException(
                    code=GameOutput.INVALID_FILE.value, message=GameOutputReason.INVALID_FILE.value
                )

            player_number = self.get_player_number(line_number)
            self.add_to_column(player_number, selected_column)

            if line_number >= self.counters * 2 - 2:
                self.is_won = self.is_winner(player_number)

            if self.is_won:
                self.winner = self.possible_winners_result[player_number - 1].value

            if not self.any_place_left(line_number):
                break

            line_number += 1

        if self.is_won:
            return self.winner

        return self.get_final_board_status(line_number)

    # noinspection PyMethodMayBeStatic
    def get_final_board_status(self, line_number):
        possible_result = (
            GameOutput.DRAW.value,
            GameOutput.INCOMPLETE.value
        )

        return possible_result[self.any_place_left(line_number)]

    def any_place_left(self, line_number):
        return line_number + 1 < self.rows * self.columns

    def is_winner(self, player_number):
        winner_substring = "".join(map(lambda x: str(x), [player_number for _ in range(self.counters)]))

        if self.__is_winner_in_row(winner_substring):
            return True

        if self.counters - 1 > sorted(self.taken_lines_in_column)[-1]:
            return False

        if self.__is_winner_in_col(winner_substring):
            return True

        if self.__is_winner_diagonal_left(winner_substring):
            return True

        if self.__is_winner_diagonal_right(winner_substring):
            return True

        return False

    def __is_winner_diagonal_right(self, winner_substring: str) -> bool:
        new_t = []

        for r in range(self.columns - 1, -1, -1):
            new_t.append([self.game_board[x][r + x] for x in range(self.rows) if r + x < self.columns])

        for r in range(1, self.rows):
            new_t.append(
                [
                    self.game_board[r + x][x] for x in range(self.columns) if
                    x + r < self.rows
                ]
            )

        for element in new_t:
            if winner_substring in "".join(map(lambda x: str(x), element)):
                return True

        return False

    def __is_winner_diagonal_left(self, winner_substring: str) -> bool:
        new_t = []
        for r in range(self.columns):
            new_t.append([self.game_board[x][r - x] for x in range(self.rows) if x <= r])

        for r in range(1, self.rows):
            new_t.append(
                [
                    self.game_board[x + r][self.columns - 1 - x] for x in range(self.rows) if
                    x + r < self.rows
                ]
            )

        for element in new_t:
            if winner_substring in "".join(map(lambda x: str(x), element)):
                return True

        return False

    def __is_winner_in_row(self, winner_substring: str) -> bool:
        for row in self.game_board:
            if winner_substring in "".join(map(lambda x: str(x), row)):
                return True

        return False

    def __is_winner_in_col(self, winner_substring: str) -> bool:
        pivot_board = [[row[i] for row in self.game_board] for i in range(self.columns)]

        for element in pivot_board:
            if winner_substring in "".join(map(lambda x: str(x), element)):
                return True

        return False

    def add_to_column(self, player_number: int, selected_column: int):
        selected_column = selected_column - 1

        if selected_column < 0:
            raise ConnectZException(
                code=GameOutput.INVALID_FILE.value, message=GameOutputReason.INVALID_FILE.value
            )

        try:
            row_index = self.taken_lines_in_column[selected_column]
        except IndexError:
            raise ConnectZException(
                code=GameOutput.INVALID_FILE.value, message=GameOutputReason.INVALID_FILE.value
            )

        row_to_take = row_index + 1
        if row_to_take > self.rows - 1:
            raise ConnectZException(
                code=GameOutput.INVALID_FILE.value, message=GameOutputReason.INVALID_FILE.value
            )

        self.game_board[row_to_take][selected_column] = player_number
        self.taken_lines_in_column[selected_column] += 1

    # noinspection PyMethodMayBeStatic
    def get_player_number(self, line_number) -> int:
        return line_number % 2 + 1

    def open_file(self):
        try:
            self.file = open(self.filename, "r")
        except (FileNotFoundError, AttributeError):
            raise ConnectZException(code=GameOutput.FILE_ERROR.value, message=GameOutputReason.FILE_ERROR.value)

    def set_game_specification(self, first_line: str) -> None:
        try:
            columns, rows, counters, *unsupported = first_line.split(" ")

            self.columns = int(columns)
            self.rows = int(rows)
            self.counters = int(counters)

            self.taken_lines_in_column = [-1 for _ in range(self.columns)]
        except ValueError:
            raise ConnectZException(
                code=GameOutput.INVALID_FILE.value, message=GameOutputReason.INVALID_FILE.value
            )

        if unsupported:
            raise ConnectZException(
                code=GameOutput.INVALID_FILE.value, message=GameOutputReason.INVALID_FILE.value
            )

        if [self.rows, self.columns][::-1][0] < self.counters:
            raise ConnectZException(
                code=GameOutput.ILLEGAL_GAME.value, message=GameOutputReason.ILLEGAL_GAME.value
            )

    def prepare_game_board(self):
        for column in range(self.rows):
            self.game_board.append([0 for _ in range(self.columns)])

    def __del__(self):
        if self.file:
            self.file.close()


def get_filename(argv) -> str or None:
    if len(argv) != 2:
        print("{}: Provide one input file".format(__file__.split("/")[-1]))
        exit(-1)

    return argv[1]


def main(argv):
    filename = get_filename(argv)

    try:
        game = ConnectZ()
        test_result = game.test_game(filename)

        print(test_result)

    except ConnectZException as err:
        print(err.code)


if __name__ == "__main__":
    main(sys.argv)
