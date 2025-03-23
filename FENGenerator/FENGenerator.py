import sys
import serial
import serial.tools.list_ports
import numpy as np
import time

BAUDRATE = 9600
INIT_TEAMS = [
    [1,0,0,0,0,0,0,-1],
    [1,0,0,0,0,0,0,-1]
]
INIT_VALUES = [
    ['K','0','0','0','0','0','0','k'],
    ['R','0','0','0','0','0','0','r']
]
class Game:
    def __init__(self, port):
        # SERIAL
        self.port = port    #the serial port to read from
        self.ser = serial.Serial(self.port, BAUDRATE)   # serial connection
        # MATRICES
        self.curr_teams = []    #current teams detected from arduino
        self.curr_values = INIT_VALUES   #curr piece values of each square (curr game state)
        self.prev_teams = INIT_TEAMS    # prev teams
        #self.prev_values = INIT_VALUES  # prev game state
        # GAME INFO
        self.done_reading = False
        self.halfturn_count = 0

    def read_teams(self):
        """
        Reads the output of the Arduino until it sees '---' (end of transmission).
        :return: Updates self.curr_teams
        """
        teams = []
        while True:  # Keep reading until '---' is encountered
            while self.ser.in_waiting == 0:
                time.sleep(0.01)  # Wait for data if buffer is empty

            line = self.ser.readline().decode("utf-8").strip()
            print(f"Currently reading: {line}")

            if line.startswith("---"):  # End of message
                self.done_reading = True
                self.halfturn_count += 1
                break

            numbers = list(map(int, line.split()))
            teams.append(numbers)

        if teams:
            self.curr_teams = teams
        else:
            print("WARNING: No valid team data received!")

    def update_curr_values(self, transition):
        """
        Uses the transition matrix and curr_teams to update
        curr_values with the current values of each piece
        :return: nothing
        """
        # movement indices: where'd the piece come from and where'd it go
        from_idx = []
        to_idx = []
        # iterating through transition matrix to detect movement
        for row in range(len(transition)):
            for col in range(len(transition[row])):
                square = transition[row][col]
                if square == 0:
                    continue
                if self.halfturn_count % 2 == 0: #if it is black's turn
                    if square == 1:
                        from_idx.append((row, col))
                    elif square == -1 or square == -2:
                        to_idx.append((row, col))
                else:                            # if it is white's turn
                    if square == 1 or square == 2:
                        to_idx.append((row, col))
                    if square == -1:
                        from_idx.append((row, col))

        # if there are no changes, there is no need to update
        if len(from_idx) == 0 or len(to_idx) == 0:
            print("No change in game state detected")
            return
        # update the piece locations
        self.curr_values[to_idx[0][0]][to_idx[0][1]] = \
            self.curr_values[from_idx[0][0]][from_idx[0][1]]
        self.curr_values[from_idx[0][0]][from_idx[0][1]] = '0'


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
game = Game(port)
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





