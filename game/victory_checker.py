import threading


class VictoryChecker:
    def __init__(self):
        self.winner = None
        self.winning_line = None
        self.lock = threading.Lock()
    
    def check_victory(self, board, row, col, player, callback=None):
        thread = threading.Thread(
            target=self._check_victory_async,
            args=(board, row, col, player, callback)
        )
        thread.daemon = True
        thread.start()
    
    def _check_victory_async(self, board, row, col, player, callback):
        directions = [
            (0, 1),
            (1, 0),
            (1, 1),
            (1, -1),
        ]
        
        winning_line = None
        for dr, dc in directions:
            line = [(row, col)]
            
            r, c = row + dr, col + dc
            while board.is_valid_position(r, c) and board.get_stone(r, c) == player:
                line.append((r, c))
                r += dr
                c += dc
            
            r, c = row - dr, col - dc
            while board.is_valid_position(r, c) and board.get_stone(r, c) == player:
                line.append((r, c))
                r -= dr
                c -= dc
            
            if len(line) >= 5:
                winning_line = line
                break
        
        with self.lock:
            if winning_line:
                self.winner = player
                self.winning_line = winning_line
        
        if callback:
            callback(winning_line is not None, player)
    
    def get_winner(self):
        with self.lock:
            return self.winner
    
    def get_winning_line(self):
        with self.lock:
            return self.winning_line
    
    def reset(self):
        with self.lock:
            self.winner = None
            self.winning_line = None
