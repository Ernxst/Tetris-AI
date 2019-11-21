"""
Autoplayer (87 Lines long):
scores 6379 with a block lookahead on seed 42
scores 5523 without the block lookahead on seed 42

Problems:
AI "rushes" decisions towards end of game
Tends to wait for an I block to fill out end columns - risky
"""
from board import Direction, Rotation
from exceptions import NoBlockException #added in
from random import Random

class Player:
    def choose_action(self, board):
        raise NotImplementedError

class RandomPlayer(Player):
    def __init__(self, seed=None):
        self.random = Random(seed)

    def choose_action(self, board):
        return self.random.choice([
            Direction.Left,
            Direction.Right,
            Direction.Down,
            Rotation.Anticlockwise,
            Rotation.Clockwise,
        ])

class Autoplayer(Player):
    def __init__(self, seed=None):
        self.scores = [0, 100, 400, 800, 1600]
        #weightings for scoring criteria
       # self.multipliers = (1.6, -3.78, -0.6, -2.31)
        self.multipliers = (0.760666, -0.510066, -0.184483, -0.35663)#, -0.15147)
        self.looked = False #if we've already looked ahead at the next block
    
    def choose_action(self, board, look_ahead=False):
        #vars representing the best possible sequence of moves to make
        best_x, best_rot, best_score, best_dir = 0, 0, -999999999999999999, None
        score = 0
        for rot in range(0, 4):
           for x in range(board.width//2+1):
               for mov_dir in (Direction.Left, Direction.Right): 
                    score = self.test_move(board, x, rot, mov_dir)
                    if score > best_score:
                        best_x,best_rot,best_score,best_dir=x,rot,score,mov_dir
        self.looked = False # reset flag so we can lookahead for the next block
        best_move = [best_dir]*abs(best_x)+[Rotation.Clockwise]*best_rot
        best_move.append(Direction.Drop) #build list of best possible moves
        if look_ahead: return score #lookahead only cares about score, not moves
        if board.score > 6100: #checking if height function works
            heights, total_height = self.get_height(board)
            print(heights)
        return best_move #fingers crossed it's actually the best move!
      
    def test_move(self, board, x, rot, mov_dir):
        dropped = False #have we already dropped the block?
        rows_removed = 0
        test_board = board.clone()
        try:
            rows_removed = self.place_block(test_board, test_board.rotate,
                                            Rotation.Clockwise,rot,rows_removed)
            rows_removed = self.place_block(test_board, test_board.move,
                                            mov_dir, x, rows_removed)
            if not dropped: test_board.move(Direction.Drop)
        except NoBlockException: pass #occurs when a block has landed and we
        #try to access it when it has become None
        #uncomment if you want to disable the lookahead
        #return self.score_move(test_board, rows_removed)
        return (self.score_move(test_board, rows_removed)+
                self.lookahead(test_board))

    def score_move(self, board, rows_removed):
        """
        In tetris, to keep the game going as long as possible:
            1: Eliminate as many rows as possible (in one go)
            2: Keep total row height as low as possible
            3: Try and keep all rows at a similar height
            4: Avoid holes that can't be filled in without clearing rows
            (5): Avoid leaving excessive pits that can only be filled in by
                 the rectangular block - in progress
        The scoring system is then based on these 4 criteria,
            - The multipliers used are a result of trial and error
        """
        score = 0
        cols, total_height = self.get_height(board)
        height_variation = self.get_variation(board, cols)
        num_of_holes = self.get_holes(board)
        num_of_pits = self.get_pits(board, cols)
        #reduces number of lines code takes
        var_list = (rows_removed, total_height, height_variation, num_of_holes)#,
                    #num_of_pits)
        for multiplier, var in zip(self.multipliers, var_list):
            score += multiplier * var
        return score

    def lookahead(self, board):
        """
        Lookahead to the next block and compute its score
        """
        score = 0
        if not self.looked: #if we haven't already looked ahead
            self.looked = True
            score = self.choose_action(board.clone(), True)
        return score
    
    def place_block(self, board, action, direction, x, rows_removed):
        """
        Helper function to either move or rotate then calculate how many rows
        it removed - reduces code repetitiveness
        """
        for m in range(0, x):
            score_before = board.score
            landed = action(direction)
            score_after = board.score
            rows_removed += self.get_rows_removed(score_before, score_after)
            if landed: break
        return rows_removed

    def get_rows_removed(self, before, after):
        """
        Calculate the number of rows removed based on the score increase
        """     
        rows_removed = 0
        score_increase = after - before
        if score_increase in self.scores and score_increase > 0:
            rows_removed += self.scores.index(score_increase)
        return rows_removed

    def get_height(self, board): #fix - max height seems to be 21
        """
        Return the total height of blocks on the board
        """
        total_height = 0
        cols = [0] * board.width #list of heights of each column
        for x in range(board.width):
            for y in range(board.height):
                if (x, y) in board.cells:
                    #point (0, 0) is in the top left corner so invert:
                    cols[x] = board.height - y
                    total_height += board.height - y
                    break #highest block already found so end this y iteration

        return cols, total_height

    def get_variation(self, board, cols):
        """
        Get the total variation in height between adjacent columns which
        represents the bumpiness of the board
        """  
        variation = 0
        #pairwise subtraction
        for m, n in  zip(cols, cols[1:]):
            variation += abs(m - n)
        return variation
    
    def get_holes(self, board):
        """
        Get the number of holes continuing with this move will produce
        A hole is defined as an empty space with at least one block on top of it
        """   
        num_of_holes = 0
        for x in range(board.width):
            for y in range(board.height):
                #point (0, 0) is in the top left corner so cell above y is y-1:
                if (x, y) not in board.cells and (x, y-1) in board.cells:
                   num_of_holes += 1
        return num_of_holes

    def get_pits(self, board, cols):
        """
        Get the number of pits continuing with this move will produce
        A pit is defined as a single column which is at least 4 blocks lower
        in height than its neighbours
        """
        pit_count = 0
        for col, next_col in zip(cols, cols[1:]):
            if abs(next_col - col) >= 4:
                pit_count += 1
        return pit_count
        
SelectedPlayer = Autoplayer
