import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import chess
from evaluate import evaluate
from search import Searcher


class EvalTests(unittest.TestCase):
    def test_start_position_is_balanced(self):
        self.assertEqual(evaluate(chess.Board()), 0)

    def test_extra_queen_is_good_for_white(self):
        board = chess.Board("rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        self.assertGreater(evaluate(board), 800)


class SearchTests(unittest.TestCase):
    def test_mate_in_one(self):
        board = chess.Board("6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1")
        move = Searcher().search(board, max_depth=3)
        self.assertEqual(move, chess.Move.from_uci("a1a8"))

    def test_takes_free_queen(self):
        board = chess.Board("4k3/8/8/3q4/8/8/8/3RK3 w - - 0 1")
        move = Searcher().search(board, max_depth=3)
        self.assertEqual(move, chess.Move.from_uci("d1d5"))

    def test_returns_legal_move_from_start(self):
        board = chess.Board()
        move = Searcher().search(board, max_depth=3)
        self.assertIn(move, board.legal_moves)


if __name__ == "__main__":
    unittest.main()
