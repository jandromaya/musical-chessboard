import sys
import serial
import serial.tools.list_ports
import numpy as np
import game_tracker
import requests

def find_arduino():
    """
    Each time the Arduino connects, a different COM port may be chosen,
    so this function finds which COM port the Arduino is connected to and
    returns it.
    :return: COM Port
    """
    ports = serial.tools.list_ports.comports()
    for i in ports:
        if "Arduino" in i.description:
            return i.device
    print("ERROR: No Arduino Found", file=sys.stderr)

def query_stockfish(fen, depth=12):
    url = "https://chess-api.com/v1"
    payload = {
        "fen": fen,
        "depth": depth,
        "variants": 1,           # Request at least one move continuation
        "maxThinkingTime": 50    # Optional, may help with some engines
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raises an error for non-2xx responses
        data = response.json()

        # Debug print: check entire response
        print("Full Response:", data)

        return data
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None

def get_harmonics(curr_values):
    black_harmonics = [0 for _ in range(8)]
    white_harmonics = [0 for _ in range(8)]
    for row in range(8):
        for column in range(8):
            if curr_values[row][column].isupper() and row > white_harmonics[column]:
                white_harmonics[column] = row + 1
            elif curr_values[row][column].islower() and (7-row) > black_harmonics[column]:
                black_harmonics[column] = 7 - row + 1
    return white_harmonics, black_harmonics

def get_avg_position(curr_values):
    # intialization of values
    black_sum, white_sum = 0, 0
    black_pieces, white_pieces = 0, 0
    piece_weights = {
        'P' : 1,
        'p' : 1,
        'R' : 2.5,
        'r' : 2.5,
        'N' : 1.5,
        'n' : 1.5,
        'B' : 1.5,
        'b' : 1.5,
        'Q' : 4.5,
        'q' : 4.5,
        'K' : 4.5,
        'k' : 4.5,
    }
    # computing weighted sum of each player's board position
    for row in range(8):
        for column in range(8):
            if curr_values[row][column].isupper():
                white_pieces += 1
                white_sum += piece_weights[curr_values[row][column]] * (8*row + column)
            if curr_values[row][column].islower():
                black_pieces += 1
                black_sum += piece_weights[curr_values[row][column]] * (8*row + column)
    # output weighted average board position
    return white_sum/white_pieces, black_sum/black_pieces






port = find_arduino()
game = game_tracker.Game(port)
with open("position.txt", "w") as file:
    print("2 2 2 2 2 2 2 2", file=file)
    print("2 2 2 2 2 2 2 2", file=file)
    print(50.0, file=file)
    
while True:
    game.read_teams()
    if game.done_reading:
        game.done_reading = False
        # making the transition matrix and printing
        transition = np.subtract(game.curr_teams, game.prev_teams).tolist()
        game.update_curr_values(transition)
        print("CURRENT TEAMS:\t", game.curr_teams)
        print("PREVIOUS TEAMS:\t", game.prev_teams)
        print("TRANS MATRIX:\t", transition)
        print("CURR_VALUES:\t", game.curr_values)
        print(f"HALFTURN COUNT:\t{game.halfturn_count}")
        print(f"LAST TAKE:\t{game.halfturn_count - game.last_take} moves ago")
        print(f"BLACK QUEEN CASTLE:\t{game.black_queen_castle_allowed}")
        print(f"BLACK KING CASTLE:\t{game.black_king_castle_allowed}")
        print(f"WHITE QUEEN CASTLE: \t{game.white_queen_castle_allowed}")
        print(f"WHITE KING CASTLE: \t{game.white_king_castle_allowed}")
        fen = game.make_fen()
        print(fen)
        result = query_stockfish(fen)
        if result:
            win_chance = result.get("winChance")
            if win_chance is None:
                win_chance = 0
            print("Win Chance: ", win_chance)
        #
        harmonics = get_harmonics(game.curr_values)
        print(harmonics)
        with open("position.txt", "w") as file:
            for row in harmonics:
                print(" ".join(str(x) for x in row), file=file)
            print(win_chance, file=file)

        game.prev_teams = [row[:] for row in game.curr_teams]