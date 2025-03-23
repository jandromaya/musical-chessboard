import sys
import serial
import serial.tools.list_ports
import numpy as np
import game_tracker

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

port = find_arduino()
game = game_tracker.Game(port)
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
        #

        game.prev_teams = [row[:] for row in game.curr_teams]