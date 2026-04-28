EMPTY = 0
BLACK = 1
WHITE = 2


class Board:
    def __init__(self, size=9):
        self.size = size
        self.grid = [[EMPTY for _ in range(size)] for _ in range(size)]
        self.move_history = []
    
    def place_stone(self, row, col, player):
        if self.is_valid_position(row, col) and self.grid[row][col] == EMPTY:
            self.grid[row][col] = player
            self.move_history.append((row, col, player))
            return True
        return False
    
    def is_valid_position(self, row, col):
        return 0 <= row < self.size and 0 <= col < self.size
    
    def get_stone(self, row, col):
        if self.is_valid_position(row, col):
            return self.grid[row][col]
        return EMPTY
    
    def get_last_move(self):
        if self.move_history:
            return self.move_history[-1]
        return None
    
    def clear(self):
        self.grid = [[EMPTY for _ in range(self.size)] for _ in range(self.size)]
        self.move_history = []
    
    def get_winning_line(self, row, col, player):
        directions = [
            (0, 1),
            (1, 0),
            (1, 1),
            (1, -1),
        ]
        
        for dr, dc in directions:
            line = [(row, col)]
            
            r, c = row + dr, col + dc
            while self.is_valid_position(r, c) and self.grid[r][c] == player:
                line.append((r, c))
                r += dr
                c += dc
            
            r, c = row - dr, col - dc
            while self.is_valid_position(r, c) and self.grid[r][c] == player:
                line.append((r, c))
                r -= dr
                c -= dc
            
            if len(line) >= 5:
                return line
        
        return None
