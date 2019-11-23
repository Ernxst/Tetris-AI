"""
Fix lookahead!
Produces a bit too many holes
Old versions of player do their best on 3rd server test whereas the newer ones
do their worst

Extra criteria:
Pits
Deepest pit
Max height
Lowest height
Average height
"""
from board import Direction, Rotation, Block
from exceptions import NoBlockException #added in
from random import Random, uniform

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
        #weightings for scoring criteria
        #below gets 187k locally on seed 42
        self.weightings = [0.8501569803801292, -0.7952277302774627, -0.17342645892226724, -0.44814605914847927]
        #self.weightings = (0.760666, -0.510066, -0.184483, -0.35663)
        self.looked = False #flag indicating if we've already looked at next block
        
    def choose_action(self, board, look_ahead=False):
        self.best_offset, self.best_rot, self.best_score = 0, 0, -9999999999999999
        for rot in range(4):
            for x_offset in range(-board.width//2, board.width//2):
                score = self.test_move(board, rot, x_offset)
                self.compare_scores(score, x_offset, rot)
        self.looked = False #reset flag for not block
        mov_dir = self.get_mov_dir(self.best_offset)
        best_move=[Rotation.Clockwise]*self.best_rot+[mov_dir]*abs(self.best_offset)
        best_move.append(Direction.Drop) #build list of best possible moves
        if look_ahead: return self.best_score #lookahead is only concerned with score
        return best_move
        
    def test_move(self, board, rot, x_offset):
        mov_land = False
        test_board = board.clone()
        score_before = test_board.score
        rot_land = self.place_block(board, test_board.rotate, rot, Rotation.Clockwise)
        """if we're not trying to move the block by 0 and the rotations have not
        caused the falling block to land, proceed to move the block"""
        if x_offset != 0 and not rot_land:
            mov_land = self.place_block(board, test_board.move, x_offset,
                             self.get_mov_dir(x_offset))
        """
        once the block drops, the next block is made to fall but a new
        next block is not assigned as we only have a 1 block lookahead
        If the rotations or movements have not caused the block to land
        proceed to drop it, otherwise this would throw a NoBlockException
        """
        if not (mov_land or rot_land):
            test_board.move(Direction.Drop) #the block does land after this
        score_after = test_board.score
        rows_removed = self.get_rows_removed(score_before, score_after)
        #return self.score_move(test_board, rows_removed)
        return (self.score_move(test_board,rows_removed)+
                self.lookahead(test_board))
            
    def score_move(self, board, rows_removed):
        """
        In tetris, to keep the game going as long as xsible:
            1: Eliminate as many rows as xsible (in one go)
            2: Keep total row height as low as possible
            3: Try and keep all rows at a similar height
            4: Avoid holes that can't be filled in without clearing rows
            (5): Avoid leaving excessive pits that can only be filled in by
                 the rectangular block - in progress
        The scoring system is then based on these 4 criteria,
            - The weightings used are a result of trial and error
        """
        score = 0
        column_heights = self.get_height(board)
        total_height = sum(column_heights)
        height_variation = self.get_variation(column_heights)
        num_of_holes = self.get_holes(board)
        #reduces number of lines code takes
        var_list = (rows_removed, total_height, height_variation, num_of_holes)
        for multiplier, var in zip(self.weightings, var_list):
            score += multiplier * var
        return score

    def lookahead(self, board):
        """
        Lookahead to the next block and compute its score
        """
        score = 0
      #  print(board.falling)
      #  input()
        if not self.looked: #if we haven't already looked ahead
            self.looked = True
            score = self.choose_action(board.clone(), True)
        return score
    
    def compare_scores(self, score, x, rot):
        """
        Update class variables if the current move produced a better score
        than the current best move
        """
        if score > self.best_score:
            self.best_offset = x
            self.best_rot = rot
            self.best_score = score

    def get_mov_dir(self, x): #get direction based on x offset
        if x < 0: return Direction.Left
        elif x > 0: return Direction.Right
        
    def get_rows_removed(self, before, after):
        """
        Calculate the number of rows removed based on the score increase
        """
        score_change = after - before
        if 105 < score_change < 130: return 1
        elif 400 < score_change < 445: return 2
        elif 805 < score_change < 855: return 3
        elif 1600 < score_change < 1650: return 4
        else: return 0

    def place_block(self, board, action, x, direction):
        """
        Helper function to either move or rotate then calculate how many rows
        it removed - reduces code repetitiveness
        """
        for move in range(abs(x)):
            landed = action(direction)
            #optimising
            if landed: return True
            #we can still drop the block, we just can't move/rotate it any
            #further to the left of right
            if board.falling.right == 9: return False
            if board.falling.left == 0: return False
        
    def get_height(self, board):
        """
        Return the total height of blocks on the board
        """
        column_heights = [0]*board.width#list to store of heights of each column
        for x in range(board.width):
            for y in range(board.height):
                if (x, y) in board.cells:
                    column_heights[x] = board.height - y
                    break #highest block already found so end this y iteration
        return column_heights

    def get_variation(self, cols):
        """
        Get the total variation in height between adjacent columns which
        represents the bumpiness of the board
        """ 
        variation = 0
        for m, n in  zip(cols, cols[1:]): #pairwise subtraction
            variation += abs(m - n)
        return variation
    
    def get_holes(self, board):
        """
        Get the number of holes continuing with this move will produce
        A hole is defined as an empty space with at least one block on top of it
        """   
        num_of_holes = 0
        for y in range(board.height):
            for x in range(board.width):
                if (x, y) not in board.cells and (x, y-1) in board.cells:
                   num_of_holes += 1
        return num_of_holes
        
SelectedPlayer = Autoplayer
