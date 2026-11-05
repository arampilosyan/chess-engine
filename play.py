#!/usr/bin/env python3
"""Play against the engine in the terminal.  Usage: python play.py [seconds_per_move]"""
import sys
import chess

from search import Searcher


def main():
    think = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0
    board = chess.Board()
    searcher = Searcher()
    side = input("Choose color (w/b) [w]: ").strip().lower()
    human = chess.BLACK if side.startswith("b") else chess.WHITE

    while not board.is_game_over():
        print()
        print(board.unicode(borders=True, invert_color=True))
        if board.turn == human:
            text = input("Your move (e.g. e4, Nf3, e2e4; 'q' to quit): ").strip()
            if text == "q":
                return
            try:
                try:
                    move = board.parse_san(text)
                except ValueError:
                    move = board.parse_uci(text)
                if move not in board.legal_moves:
                    raise ValueError
            except ValueError:
                print("Illegal or unreadable move, try again.")
                continue
        else:
            def show(depth, score, nodes, elapsed, pv):
                print(f"  depth {depth:2d}  score {score / 100:+.2f}  nodes {nodes}")
            move = searcher.search(board, time_limit=think, info=show)
            print(f"Engine plays: {board.san(move)}")
        board.push(move)

    print()
    print(board.unicode(borders=True, invert_color=True))
    print("Game over:", board.result(), board.outcome().termination.name)


if __name__ == "__main__":
    main()
