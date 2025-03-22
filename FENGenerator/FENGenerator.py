import sys


import serial
import serial.tools.list_ports
BAUDRATE = 9600
INIT_TEAMS = [
    [1,0,0,0,0,0,0,-1],
    [1,0,0,0,0,0,0,-1]
]
class Game:
    def __init__(self, port):
        self.port = port
        self.curr_teams = []
        self.prev_teams = INIT_TEAMS
        self.ser = serial.Serial(self.port, BAUDRATE)
        self.done_reading = False

    def read_teams(self):
        """
        Reads the output of the arduino
        :return: prints the output of the arduino to the console
        """
        teams = []
        while self.ser.in_waiting > 0:
            line = self.ser.readline().decode("utf-8").strip()
            if line.startswith("-"):
                self.done_reading = True
                break
            numbers = list(map(int, line.split()))
            teams.append(numbers)
        if teams:
            self.curr_teams = teams

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
        print("CURRENT TEAMS:\t", game.curr_teams)
        print("PREVIOUS TEAMS:\t", game.prev_teams)
        game.prev_teams = game.curr_teams
        game.done_reading = False

