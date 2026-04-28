import pygame
import threading
import time
import os
from .board import Board, BLACK, WHITE, EMPTY
from .victory_checker import VictoryChecker
from . import SoundManager


class GameState:
    START = 0
    PLAYING = 1
    PAUSED = 2
    BLACK_WIN = 3
    WHITE_WIN = 4
    DRAW = 5
    GAME_OVER = 6


class Game:
    def __init__(self, screen_width=800, screen_height=700):
        pygame.init()
        pygame.font.init()
        
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("五子棋")
        
        self.board_size = 9
        self.board = Board(self.board_size)
        self.victory_checker = VictoryChecker()
        
        self.cell_size = 60
        self._calculate_layout()
        
        self.current_player = BLACK
        self.game_state = GameState.START
        
        self.time_limit = 20
        self.time_left = self.time_limit
        self.last_time_update = time.time()
        
        self.black_pause_used = False
        self.white_pause_used = False
        self.pause_start_time = 0
        self.time_before_pause = 0
        
        self.sound_manager = SoundManager()
        
        self.victory_callback = None
        self.winning_line = None
        self.winner = None
        self.is_draw = False
        
        self._init_ui()
        
    def _calculate_layout(self):
        info_bar_height = 70
        button_bar_height = 60
        
        board_grid_height = (self.board_size - 1) * self.cell_size
        stone_radius = self.cell_size // 2
        
        margin_size = 20
        
        total_content = info_bar_height + margin_size + board_grid_height + stone_radius + margin_size + button_bar_height
        remaining = self.screen_height - total_content
        
        top_margin = remaining // 2 if remaining > 0 else 0
        
        self.info_bar_y = top_margin
        self.board_offset_y = top_margin + info_bar_height + margin_size
        self.board_offset_x = (self.screen_width - (self.board_size - 1) * self.cell_size) // 2
        self.button_bar_y = self.board_offset_y + board_grid_height + stone_radius + margin_size
        
        print(f"布局计算:")
        print(f"  顶部边距: {top_margin}px")
        print(f"  信息栏Y: {self.info_bar_y}px")
        print(f"  棋盘位置: ({self.board_offset_x}, {self.board_offset_y})")
        print(f"  棋盘底部(含棋子): {self.board_offset_y + board_grid_height + stone_radius}px")
        print(f"  按钮栏Y: {self.button_bar_y}px")
        print(f"  棋盘到按钮间距: {self.button_bar_y - (self.board_offset_y + board_grid_height + stone_radius)}px")
        
    def _init_ui(self):
        self.font_large = None
        self.font_medium = None
        self.font_small = None
        
        chinese_fonts = [
            ("PingFang SC", "苹方"),
            ("Heiti SC", "黑体"),
            ("STHeiti", "华文黑体"),
            ("Songti SC", "宋体"),
            ("KaiTi", "楷体"),
            ("Arial Unicode MS", "Arial Unicode"),
            ("SimHei", "黑体"),
            ("Microsoft YaHei", "微软雅黑"),
            ("simsun", "宋体"),
            ("msyh", "微软雅黑"),
        ]
        
        for font_name, font_display in chinese_fonts:
            try:
                test_font = pygame.font.SysFont(font_name, 24)
                test_surface = test_font.render("测试中文", True, (0, 0, 0))
                if test_surface.get_width() > 50:
                    print(f"找到支持中文的字体: {font_name} ({font_display})")
                    self.font_large = pygame.font.SysFont(font_name, 52)
                    self.font_medium = pygame.font.SysFont(font_name, 32)
                    self.font_small = pygame.font.SysFont(font_name, 24)
                    break
            except:
                continue
        
        if self.font_large is None:
            print("警告: 未找到支持中文的系统字体，尝试使用备用方案")
            try:
                available_fonts = pygame.font.get_fonts()
                for font_name in available_fonts:
                    if any(cn in font_name.lower() for cn in ['hei', 'song', 'kai', 'ming', 'cn', 'chinese', 'unicode']):
                        try:
                            test_font = pygame.font.SysFont(font_name, 24)
                            test_surface = test_font.render("测试", True, (0, 0, 0))
                            if test_surface.get_width() > 20:
                                print(f"找到可能支持中文的字体: {font_name}")
                                self.font_large = pygame.font.SysFont(font_name, 52)
                                self.font_medium = pygame.font.SysFont(font_name, 32)
                                self.font_small = pygame.font.SysFont(font_name, 24)
                                break
                        except:
                            continue
            except:
                pass
        
        if self.font_large is None:
            print("警告: 系统中文字体加载失败，使用默认字体（中文可能显示为方框）")
            self.font_large = pygame.font.Font(None, 52)
            self.font_medium = pygame.font.Font(None, 32)
            self.font_small = pygame.font.Font(None, 24)
        
        self.button_color = (70, 130, 180)
        self.button_hover_color = (100, 160, 210)
        self.button_disabled_color = (150, 150, 150)
        self.text_color = (255, 255, 255)
        self.bg_color = (240, 217, 181)
        self.dialog_bg_color = (255, 255, 255)
        self.dialog_border_color = (50, 50, 50)
        
        button_width = 130
        button_height = 45
        
        board_left = self.board_offset_x
        board_right = self.board_offset_x + (self.board_size - 1) * self.cell_size
        
        self.buttons = {
            'pause': {
                'rect': pygame.Rect(board_left, self.button_bar_y, button_width, button_height),
                'text': '暂停',
                'enabled': True
            },
            'resign': {
                'rect': pygame.Rect(board_right - button_width, self.button_bar_y, button_width, button_height),
                'text': '认输',
                'enabled': True
            }
        }
        
        dialog_width = 320
        dialog_height = 200
        dialog_x = (self.screen_width - dialog_width) // 2
        dialog_y = (self.screen_height - dialog_height) // 2
        
        self.start_dialog = {
            'rect': pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height),
            'start_button': pygame.Rect(
                dialog_x + (dialog_width - 140) // 2,
                dialog_y + dialog_height - 80,
                140, 50
            )
        }
        
        self.end_dialog = {
            'rect': pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height),
            'restart_button': pygame.Rect(
                dialog_x + (dialog_width - 140) // 2,
                dialog_y + dialog_height - 80,
                140, 50
            )
        }
    
    def _update_timer(self):
        if self.game_state == GameState.PLAYING:
            current_time = time.time()
            delta_time = current_time - self.last_time_update
            self.last_time_update = current_time
            
            self.time_left -= delta_time
            
            if self.time_left <= 0:
                self.time_left = 0
                self._handle_timeout()
    
    def _handle_timeout(self):
        if self.current_player == BLACK:
            self.winner = WHITE
            self.game_state = GameState.WHITE_WIN
        else:
            self.winner = BLACK
            self.game_state = GameState.BLACK_WIN
    
    def _start_game(self):
        self.game_state = GameState.PLAYING
        self.last_time_update = time.time()
        print("游戏开始！")
    
    def _handle_click(self, pos):
        x, y = pos
        
        if self.game_state == GameState.START:
            if self.start_dialog['start_button'].collidepoint(x, y):
                self._start_game()
            return
        
        if self.game_state in [GameState.BLACK_WIN, GameState.WHITE_WIN, GameState.DRAW]:
            if self.end_dialog['restart_button'].collidepoint(x, y):
                self._restart()
            return
        
        if self.game_state in [GameState.PLAYING, GameState.PAUSED]:
            for button_name, button in self.buttons.items():
                if button['rect'].collidepoint(x, y):
                    self._handle_button_click(button_name)
                    return
        
        if self._is_board_click(pos):
            row, col = self._screen_to_board(pos)
            self._place_stone(row, col)
    
    def _is_board_click(self, pos):
        x, y = pos
        min_x = self.board_offset_x - self.cell_size // 2
        max_x = self.board_offset_x + (self.board_size - 1) * self.cell_size + self.cell_size // 2
        min_y = self.board_offset_y - self.cell_size // 2
        max_y = self.board_offset_y + (self.board_size - 1) * self.cell_size + self.cell_size // 2
        return min_x <= x <= max_x and min_y <= y <= max_y
    
    def _screen_to_board(self, pos):
        x, y = pos
        col = round((x - self.board_offset_x) / self.cell_size)
        row = round((y - self.board_offset_y) / self.cell_size)
        return row, col
    
    def _board_to_screen(self, row, col):
        x = self.board_offset_x + col * self.cell_size
        y = self.board_offset_y + row * self.cell_size
        return x, y
    
    def _place_stone(self, row, col):
        if self.game_state == GameState.START:
            return
        
        if self.game_state == GameState.PAUSED:
            self._resume_game()
        
        if self.game_state != GameState.PLAYING:
            return
        
        if self.board.place_stone(row, col, self.current_player):
            if self.current_player == BLACK:
                self.sound_manager.play_black_stone()
            else:
                self.sound_manager.play_white_stone()
            
            self.victory_checker.check_victory(
                self.board, row, col, self.current_player,
                callback=self._on_victory_checked
            )
            
            move_count = len(self.board.move_history)
            total_positions = self.board_size * self.board_size
            
            self._switch_player()
            
            if move_count >= total_positions:
                self._check_draw_after_delay(row, col)
    
    def _check_draw_after_delay(self, row, col):
        def check_draw():
            time.sleep(0.1)
            
            current_winner = self.victory_checker.get_winner()
            if current_winner is None:
                winning_line = self.board.get_winning_line(row, col, self.current_player)
                if winning_line is None:
                    for r in range(self.board_size):
                        for c in range(self.board_size):
                            stone = self.board.get_stone(r, c)
                            if stone != EMPTY:
                                line = self.board.get_winning_line(r, c, stone)
                                if line is not None:
                                    return
                    
                    self.is_draw = True
                    self.game_state = GameState.DRAW
        
        thread = threading.Thread(target=check_draw)
        thread.daemon = True
        thread.start()
    
    def _on_victory_checked(self, has_won, player):
        if has_won:
            self.winner = player
            self.winning_line = self.victory_checker.get_winning_line()
            if player == BLACK:
                self.game_state = GameState.BLACK_WIN
            else:
                self.game_state = GameState.WHITE_WIN
    
    def _switch_player(self):
        self.current_player = WHITE if self.current_player == BLACK else BLACK
        self.time_left = self.time_limit
        self.last_time_update = time.time()
    
    def _handle_button_click(self, button_name):
        if button_name == 'pause':
            self._toggle_pause()
        elif button_name == 'resign':
            self._handle_resign()
    
    def _toggle_pause(self):
        if self.game_state == GameState.PLAYING:
            self._pause_game()
        elif self.game_state == GameState.PAUSED:
            self._resume_game()
    
    def _pause_game(self):
        if self.current_player == BLACK and not self.black_pause_used:
            self.black_pause_used = True
            self.game_state = GameState.PAUSED
            self.time_before_pause = self.time_left
            self.pause_start_time = time.time()
        elif self.current_player == WHITE and not self.white_pause_used:
            self.white_pause_used = True
            self.game_state = GameState.PAUSED
            self.time_before_pause = self.time_left
            self.pause_start_time = time.time()
    
    def _resume_game(self):
        if self.game_state == GameState.PAUSED:
            self.game_state = GameState.PLAYING
            self.time_left = self.time_before_pause
            self.last_time_update = time.time()
    
    def _handle_resign(self):
        if self.game_state not in [GameState.PLAYING, GameState.PAUSED]:
            return
        
        if self.current_player == BLACK:
            self.winner = WHITE
            self.game_state = GameState.WHITE_WIN
        else:
            self.winner = BLACK
            self.game_state = GameState.BLACK_WIN
    
    def _restart(self):
        self.board.clear()
        self.victory_checker.reset()
        self.current_player = BLACK
        self.game_state = GameState.PLAYING
        self.time_left = self.time_limit
        self.last_time_update = time.time()
        self.black_pause_used = False
        self.white_pause_used = False
        self.winner = None
        self.winning_line = None
        self.time_before_pause = 0
        self.is_draw = False
    
    def _draw(self):
        self.screen.fill(self.bg_color)
        
        if self.game_state == GameState.START:
            self._draw_start_dialog()
        else:
            self._draw_board()
            self._draw_stones()
            self._draw_winning_line()
            self._draw_ui()
            
            if self.game_state in [GameState.BLACK_WIN, GameState.WHITE_WIN, GameState.DRAW]:
                self._draw_end_dialog()
        
        pygame.display.flip()
    
    def _draw_start_dialog(self):
        dialog = self.start_dialog
        rect = dialog['rect']
        
        pygame.draw.rect(self.screen, self.dialog_bg_color, rect, border_radius=15)
        pygame.draw.rect(self.screen, self.dialog_border_color, rect, 3, border_radius=15)
        
        title_surface = self.font_large.render("五子棋", True, (50, 50, 50))
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, rect.y + 50))
        self.screen.blit(title_surface, title_rect)
        
        subtitle_surface = self.font_medium.render("点击开始", True, (80, 80, 80))
        subtitle_rect = subtitle_surface.get_rect(center=(self.screen_width // 2, rect.y + 95))
        self.screen.blit(subtitle_surface, subtitle_rect)
        
        self._draw_dialog_button(dialog['start_button'], "开始游戏")
    
    def _draw_end_dialog(self):
        dialog = self.end_dialog
        rect = dialog['rect']
        
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 80))
        self.screen.blit(overlay, (0, 0))
        
        pygame.draw.rect(self.screen, self.dialog_bg_color, rect, border_radius=15)
        pygame.draw.rect(self.screen, self.dialog_border_color, rect, 3, border_radius=15)
        
        title_surface = self.font_large.render("游戏结束", True, (50, 50, 50))
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, rect.y + 45))
        self.screen.blit(title_surface, title_rect)
        
        if self.is_draw:
            result_text = "平局!"
            result_color = (100, 100, 100)
        else:
            result_text = "黑方获胜!" if self.winner == BLACK else "白方获胜!"
            result_color = (0, 0, 0) if self.winner == BLACK else (80, 80, 80)
        
        result_surface = self.font_medium.render(result_text, True, result_color)
        result_rect = result_surface.get_rect(center=(self.screen_width // 2, rect.y + 90))
        self.screen.blit(result_surface, result_rect)
        
        self._draw_dialog_button(dialog['restart_button'], "重新开始")
    
    def _draw_dialog_button(self, rect, text):
        mouse_pos = pygame.mouse.get_pos()
        
        if rect.collidepoint(mouse_pos):
            color = self.button_hover_color
        else:
            color = self.button_color
        
        pygame.draw.rect(self.screen, color, rect, border_radius=10)
        pygame.draw.rect(self.screen, (40, 40, 40), rect, 2, border_radius=10)
        
        text_surface = self.font_medium.render(text, True, self.text_color)
        text_rect = text_surface.get_rect(center=rect.center)
        self.screen.blit(text_surface, text_rect)
    
    def _draw_board(self):
        for i in range(self.board_size):
            start_x = self.board_offset_x
            end_x = self.board_offset_x + (self.board_size - 1) * self.cell_size
            y = self.board_offset_y + i * self.cell_size
            pygame.draw.line(self.screen, (0, 0, 0), (start_x, y), (end_x, y), 2)
            
            start_y = self.board_offset_y
            end_y = self.board_offset_y + (self.board_size - 1) * self.cell_size
            x = self.board_offset_x + i * self.cell_size
            pygame.draw.line(self.screen, (0, 0, 0), (x, start_y), (x, end_y), 2)
        
        star_points = [
            (2, 2), (2, 4), (2, 6),
            (4, 2), (4, 4), (4, 6),
            (6, 2), (6, 4), (6, 6)
        ]
        for row, col in star_points:
            x, y = self._board_to_screen(row, col)
            pygame.draw.circle(self.screen, (0, 0, 0), (int(x), int(y)), 5)
    
    def _draw_stones(self):
        for row in range(self.board_size):
            for col in range(self.board_size):
                stone = self.board.get_stone(row, col)
                if stone != EMPTY:
                    x, y = self._board_to_screen(row, col)
                    color = (0, 0, 0) if stone == BLACK else (255, 255, 255)
                    outline_color = (80, 80, 80) if stone == WHITE else (0, 0, 0)
                    
                    pygame.draw.circle(self.screen, color, (int(x), int(y)), self.cell_size // 2 - 4)
                    pygame.draw.circle(self.screen, outline_color, (int(x), int(y)), self.cell_size // 2 - 4, 2)
    
    def _draw_winning_line(self):
        if self.winning_line:
            for row, col in self.winning_line:
                x, y = self._board_to_screen(row, col)
                pygame.draw.rect(self.screen, (255, 0, 0), 
                               (int(x) - 10, int(y) - 10, 20, 20), 4)
    
    def _draw_ui(self):
        info_y = self.info_bar_y
        
        current_player_text = "当前: 黑方" if self.current_player == BLACK else "当前: 白方"
        current_player_color = (0, 0, 0) if self.current_player == BLACK else (80, 80, 80)
        text_surface = self.font_medium.render(current_player_text, True, current_player_color)
        self.screen.blit(text_surface, (50, info_y))
        
        time_text = f"时间: {max(0, int(self.time_left))}秒"
        time_color = (255, 0, 0) if self.time_left <= 5 else (0, 0, 0)
        time_surface = self.font_medium.render(time_text, True, time_color)
        self.screen.blit(time_surface, (220, info_y))
        
        black_pause_text = "黑方暂停: 已使用" if self.black_pause_used else "黑方暂停: 可用"
        white_pause_text = "白方暂停: 已使用" if self.white_pause_used else "白方暂停: 可用"
        
        black_pause_color = (150, 150, 150) if self.black_pause_used else (0, 0, 0)
        white_pause_color = (150, 150, 150) if self.white_pause_used else (0, 0, 0)
        
        black_pause_surface = self.font_small.render(black_pause_text, True, black_pause_color)
        white_pause_surface = self.font_small.render(white_pause_text, True, white_pause_color)
        
        self.screen.blit(black_pause_surface, (520, info_y))
        self.screen.blit(white_pause_surface, (520, info_y + 30))
        
        if self.game_state == GameState.PAUSED:
            pause_surface = self.font_large.render("游戏暂停", True, (255, 0, 0))
            pause_rect = pause_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            self.screen.blit(pause_surface, pause_rect)
        
        if self.game_state in [GameState.PLAYING, GameState.PAUSED]:
            self._draw_buttons()
    
    def _draw_buttons(self):
        mouse_pos = pygame.mouse.get_pos()
        
        for button_name, button in self.buttons.items():
            rect = button['rect']
            text = button['text']
            
            if button_name == 'pause':
                if self.game_state == GameState.PLAYING:
                    current_player_used = (self.current_player == BLACK and self.black_pause_used) or \
                                         (self.current_player == WHITE and self.white_pause_used)
                    enabled = not current_player_used
                    text = '暂停'
                elif self.game_state == GameState.PAUSED:
                    enabled = True
                    text = '继续'
                else:
                    enabled = False
                    text = '暂停'
            else:
                enabled = True
            
            if enabled:
                if rect.collidepoint(mouse_pos):
                    color = self.button_hover_color
                else:
                    color = self.button_color
            else:
                color = self.button_disabled_color
            
            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            pygame.draw.rect(self.screen, (40, 40, 40), rect, 2, border_radius=8)
            
            text_surface = self.font_small.render(text, True, self.text_color)
            text_rect = text_surface.get_rect(center=rect.center)
            self.screen.blit(text_surface, text_rect)
    
    def run(self):
        clock = pygame.time.Clock()
        running = True
        
        print(f"游戏窗口大小: {self.screen_width}x{self.screen_height}")
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self._handle_click(event.pos)
            
            self._update_timer()
            self._draw()
            clock.tick(60)
        
        pygame.quit()
