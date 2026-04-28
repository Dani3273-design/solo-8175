#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
五子棋游戏
基于Pygame实现的五子棋游戏
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game.game import Game


def main():
    """
    游戏入口函数
    """
    game = Game(screen_width=800, screen_height=700)
    game.run()


if __name__ == "__main__":
    main()
