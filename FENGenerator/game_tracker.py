import serial
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
        # GAME INFO
        self.done_reading = False
        self.halfturn_count = 0
        self.last_take = 0
        # CASTLING AVAILABILITY
        self.black_king_castle_allowed = True
        self.black_queen_castle_allowed = True
        self.white_king_castle_allowed = True
        self.white_queen_castle_allowed = True

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
        curr_values with the current values of each piece. Transition
        matrix is equal to curr_teams - prev_teams or \
         np.subtract(curr_teams, prev_teams)
        :return: nothing, just updates curr_values
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
                if square == 2 or square == -2:
                    self.last_take = self.halfturn_count

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
        # if two pieces moved at the same time, there was castling
        if len(from_idx) == 2 and len(to_idx) == 2:
            print("castling")
            self._handle_castling(from_idx, to_idx)
            return
        # if there are otherwise two "to" positions, we have en passant
        if len(to_idx) == 2:
            print("en passant")
            self._handle_en_passant(from_idx, to_idx)
            return
        self._update_castle_availability(from_idx)
        # update the piece locations
        self.curr_values[to_idx[0][0]][to_idx[0][1]] = \
            self.curr_values[from_idx[0][0]][from_idx[0][1]]
        self.curr_values[from_idx[0][0]][from_idx[0][1]] = '0'

    def _handle_en_passant(self, from_idx, to_idx):
        """
        This function handles the game state updates whenever there
        are any en passant movements
        :param from_idx: the detected indices where pieces moved from
        :param to_idx: the detected indices for where pieces moved to
        :return: nothing
        """
        if self.halfturn_count % 2 == 0:    # if it is black's turn
            # if black took with en passant, want to go towards row 0
            if to_idx[0][0] < to_idx[1][0]:
                taking = to_idx[0]
                taken = to_idx[1]
            else:
                taking = to_idx[1]
                taken = to_idx[0]
        else:                               # if it is white's turn
            if to_idx[0][0] > to_idx[1][0]:
                taking = to_idx[0]
                taken = to_idx[1]
            else:
                taking = to_idx[1]
                taken = to_idx[0]
        # updating the game state
        self.curr_values[taking[0]][taking[1]] = \
            self.curr_values[from_idx[0][0]][from_idx[0][1]]
        self.curr_values[taken[0]][taken[1]] = '0'
        self.curr_values[from_idx[0][0]][from_idx[0][1]] = '0'

    def _handle_castling(self, from_idx, to_idx):
        """
        Handles game states in which castling is detected (two pieces moved
        at once)
        :param from_idx: indices from where pieces moved
        :param to_idx: indices pieces moved to
        :return: nothing, just updates self.curr_values
        """
        # castling follows the following pattern:
        # highest from -> lowest to
        # lowest from -> highest to

        # getting lowest from, highest from
        if from_idx[0][1] < from_idx[1][1]:
            lowest_from = from_idx[0]
            highest_from = from_idx[1]
        else:
            lowest_from = from_idx[1]
            highest_from = from_idx[0]
        #getting lowest to, highest to
        if to_idx[0][1] < to_idx[1][1]:
            lowest_to = to_idx[0]
            highest_to = to_idx[1]
        else:
            lowest_to = to_idx[1]
            highest_to = to_idx[0]

        #updating game state in self.curr_values
        self.curr_values[lowest_to[0]][lowest_to[1]] = \
            self.curr_values[highest_from[0]][highest_from[1]]
        self.curr_values[highest_to[0]][highest_to[1]] = \
            self.curr_values[lowest_from[0]][lowest_from[1]]
        self.curr_values[highest_from[0]][highest_from[1]] = '0'
        self.curr_values[lowest_from[0]][lowest_from[1]] = '0'
        # update castling availability
        if self.halfturn_count % 2 == 0: #if it is black's turn
            self.black_king_castle_allowed = False
            self.black_queen_castle_allowed = False
        else:
            self.white_king_castle_allowed = False
            self.white_queen_castle_allowed = False


    def _update_castle_availability(self, from_idx):
        """
        Handles castling availability for normal (non-castle) moves. If
        the king moves, no castling allowed. If Q-side rook moves,
        q-side castling not allowed. If K-side rook moves, k-side castling
        not allowed
        :param from_idx: index where pieces are moving from
        :return: nothing, just updates castling availability vars
        """
        # if no rook or kings moved, castling availability is not affected
        if not self._rook_or_king_moved(from_idx):
            return
        # if no castling is available anyway, nothing to change
        if not self.black_king_castle_allowed and not self.black_queen_castle_allowed \
           and not self.white_king_castle_allowed and self.white_queen_castle_allowed:
            return
        # if a rook or king moved AND there is something to change, update
        piece = self.curr_values[from_idx[0][0]][from_idx[0][1]]
        if piece == 'k':
            self.black_king_castle_allowed = False
        elif piece == 'K':
            self.white_king_castle_allowed = False
        elif piece == 'r':
            if from_idx[0][1] < 4: #queen side rook
                self.black_queen_castle_allowed = False
            else:                  #king side rook
                self.black_king_castle_allowed = False
        else:
            if from_idx[0][1] < 4:  #queen side rook
                self.white_queen_castle_allowed = False
            else:                   #king side rook
                self.white_king_castle_allowed = False

    def _rook_or_king_moved(self, from_idx):
        piece = self.curr_values[from_idx[0][0]][from_idx[0][1]]
        return  piece == 'k' or \
                piece == 'K' or \
                piece == 'r' or \
                piece == 'R'
