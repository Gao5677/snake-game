#!/usr/bin/env python3
import curses
import time
import random
import sys
from collections import deque

CONTROLS = {
    "w": "UP", "k": "UP",
    "s": "DOWN", "j": "DOWN",
    "a": "LEFT", "h": "LEFT",
    "d": "RIGHT", "l": "RIGHT",
}

DIRECTIONS = {
    "UP": (-1, 0),
    "DOWN": (1, 0),
    "LEFT": (0, -2),
    "RIGHT": (0, 2),
}

OPPOSITE = {
    "UP": "DOWN",
    "DOWN": "UP",
    "LEFT": "RIGHT",
    "RIGHT": "LEFT",
}


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)
    stdscr.timeout(100)

    max_y, max_x = stdscr.getmaxyx()
    h, w = max_y - 3, max_x - 2

    if h < 10 or w < 30:
        stdscr.addstr(0, 0, "Terminal too small! Resize and try again.")
        stdscr.refresh()
        time.sleep(2)
        return

    snake = deque()
    start_y, start_x = h // 2, (w // 4) * 2
    for i in range(3):
        snake.append((start_y, start_x - i * 2))

    direction = "RIGHT"
    food = spawn_food(snake, h, w)
    score = 0
    speed = 100
    paused = False
    game_over = False
    win = False

    while True:
        key = None
        try:
            key = stdscr.getkey()
            if len(key) == 1:
                key = key.lower()
        except curses.error:
            pass

        if key == "q":
            break
        elif key == "p":
            paused = not paused
        elif key == "r" and game_over:
            snake = deque()
            for i in range(3):
                snake.append((start_y, start_x - i * 2))
            direction = "RIGHT"
            food = spawn_food(snake, h, w)
            if food is None:
                game_over = True
                win = True
                continue
            score = 0
            speed = 100
            game_over = False
            win = False
            paused = False
        elif key in CONTROLS and not game_over:
            new_dir = CONTROLS[key]
            if new_dir != OPPOSITE[direction]:
                direction = new_dir
        elif not game_over:
            if key == "KEY_UP" and direction != "DOWN":
                direction = "UP"
            elif key == "KEY_DOWN" and direction != "UP":
                direction = "DOWN"
            elif key == "KEY_LEFT" and direction != "RIGHT":
                direction = "LEFT"
            elif key == "KEY_RIGHT" and direction != "LEFT":
                direction = "RIGHT"

        if paused or game_over:
            stdscr.clear()
            draw_border(stdscr, max_y, max_x)
            draw_snake(stdscr, snake)
            if food is not None:
                stdscr.addch(food[0] + 1, food[1] + 1, "*", curses.A_BOLD)
            if paused:
                draw_centered(stdscr, h // 2, w, "PAUSED", curses.A_BLINK)
                draw_centered(stdscr, h // 2 + 1, w, "Press P to resume")
            else:
                if win:
                    draw_centered(stdscr, h // 2, w, "YOU WIN!", curses.A_BOLD)
                else:
                    draw_centered(stdscr, h // 2, w, "GAME OVER", curses.A_BOLD)
                draw_centered(stdscr, h // 2 + 1, w, f"Score: {score}")
                draw_centered(stdscr, h // 2 + 2, w, "Press R to restart or Q to quit")
            draw_status(stdscr, max_y, w, score, len(snake))
            stdscr.refresh()
            continue

        head_y, head_x = snake[0]
        dy, dx = DIRECTIONS[direction]
        new_head = (head_y + dy, head_x + dx)

        if (new_head[0] <= 0 or new_head[0] >= h - 1 or
                new_head[1] <= 0 or new_head[1] >= w - 1):
            game_over = True
            continue

        if new_head in snake and new_head != snake[-1]:
            game_over = True
            continue

        snake.appendleft(new_head)

        if new_head == food:
            score += 10
            food = spawn_food(snake, h, w)
            if food is None:
                game_over = True
                win = True
                continue
            speed = max(30, speed - 2)
            stdscr.timeout(speed)
        else:
            snake.pop()

        stdscr.clear()
        draw_border(stdscr, max_y, max_x)
        draw_snake(stdscr, snake)
        if food is not None:
            stdscr.addch(food[0] + 1, food[1] + 1, "*", curses.color_pair(2) | curses.A_BOLD)
        draw_status(stdscr, max_y, w, score, len(snake))
        stdscr.refresh()


def spawn_food(snake, h, w):
    empty = [(y, x) for y in range(1, h - 1)
             for x in range(2, w - 1, 2) if (y, x) not in snake]
    if not empty:
        return None
    return random.choice(empty)


def draw_border(stdscr, max_y, max_x):
    border = curses.color_pair(3)
    for y in range(1, max_y - 1):
        _try_addch(stdscr, y, 0, "|", border)
        _try_addch(stdscr, y, max_x - 1, "|", border)
    for x in range(1, max_x - 1):
        _try_addch(stdscr, 0, x, "-", border)
        _try_addch(stdscr, max_y - 1, x, "-", border)
    _try_addch(stdscr, 0, 0, "+", border)
    _try_addch(stdscr, 0, max_x - 1, "+", border)
    _try_addch(stdscr, max_y - 1, 0, "+", border)
    _try_addch(stdscr, max_y - 1, max_x - 1, "+", border)


def _try_addch(stdscr, y, x, ch, attr):
    try:
        stdscr.addch(y, x, ch, attr)
    except curses.error:
        pass


def draw_snake(stdscr, snake):
    color = curses.color_pair(1)
    head_color = curses.color_pair(1) | curses.A_BOLD
    for i, (y, x) in enumerate(snake):
        ch = "O" if i == 0 else "o"
        attr = head_color if i == 0 else color
        try:
            stdscr.addstr(y + 1, x + 1, ch, attr)
        except curses.error:
            pass


def draw_status(stdscr, max_y, w, score, length):
    status = f" Score: {score}  |  Length: {length}  |  P: Pause  |  Q: Quit "
    try:
        stdscr.addstr(max_y - 2, 1, status[:w - 2], curses.A_REVERSE)
    except curses.error:
        pass


def draw_centered(stdscr, y, w, text, attr=0):
    x = 1 + max(0, (w - len(text)) // 2)
    try:
        stdscr.addstr(y, x, text, attr)
    except curses.error:
        pass


def setup_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)
    curses.init_pair(2, curses.COLOR_RED, -1)
    curses.init_pair(3, curses.COLOR_CYAN, -1)


if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Snake Game - Terminal Edition")
        print()
        print("Controls:")
        print("  Arrow keys or W/A/S/D  -  Move")
        print("  H/J/K/L               -  Move (vim style)")
        print("  P                     -  Pause")
        print("  R                   -  Restart (after game over)")
        print("  Q                   -  Quit")
        sys.exit(0)

    curses.wrapper(lambda stdscr: setup_colors() or main(stdscr))
