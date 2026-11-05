#!/usr/bin/env python3
"""UCI protocol front-end. Works with Arena, Cute Chess, lichess-bot, etc."""
import sys
import threading
import chess

from search import Searcher, MATE, MATE_BOUND

NAME = "PyAlphaBeta 1.0"
AUTHOR = "you"


def score_str(score):
    if abs(score) > MATE_BOUND:
        moves = (MATE - abs(score) + 1) // 2
        return f"mate {moves if score > 0 else -moves}"
    return f"cp {score}"


def send(line):
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def set_position(board_holder, tokens):
    if tokens[0] == "startpos":
        board = chess.Board()
        rest = tokens[1:]
    elif tokens[0] == "fen":
        idx = tokens.index("moves") if "moves" in tokens else len(tokens)
        board = chess.Board(" ".join(tokens[1:idx]))
        rest = tokens[idx:]
    else:
        return
    if rest and rest[0] == "moves":
        for mv in rest[1:]:
            board.push_uci(mv)
    board_holder[0] = board


def compute_limits(board, p):
    """Return (max_depth, time_limit_seconds_or_None)."""
    if "movetime" in p:
        return 64, max(0.05, p["movetime"] / 1000 - 0.05)
    if "wtime" in p or "btime" in p:
        key, ikey = ("wtime", "winc") if board.turn == chess.WHITE else ("btime", "binc")
        remaining = p.get(key, 60000) / 1000
        inc = p.get(ikey, 0) / 1000
        mtg = p.get("movestogo", 30) or 30
        limit = remaining / mtg + inc * 0.8
        limit = min(limit, remaining * 0.5)
        return 64, max(0.05, limit)
    if "depth" in p:
        return p["depth"], None
    return 64, None  # infinite: runs until "stop"


def main():
    board_holder = [chess.Board()]
    searcher = Searcher()
    worker = None

    def info_cb(depth, score, nodes, elapsed, pv):
        nps = int(nodes / elapsed) if elapsed > 0 else 0
        send(f"info depth {depth} score {score_str(score)} nodes {nodes} "
             f"nps {nps} time {int(elapsed * 1000)} pv {' '.join(m.uci() for m in pv)}")

    def run_search(board, max_depth, time_limit):
        move = searcher.search(board, max_depth, time_limit, info_cb)
        send(f"bestmove {move.uci() if move else '0000'}")

    for line in sys.stdin:
        tokens = line.split()
        if not tokens:
            continue
        cmd = tokens[0]

        if cmd == "uci":
            send(f"id name {NAME}")
            send(f"id author {AUTHOR}")
            send("uciok")
        elif cmd == "isready":
            send("readyok")
        elif cmd == "ucinewgame":
            searcher.tt.clear()
            board_holder[0] = chess.Board()
        elif cmd == "position":
            set_position(board_holder, tokens[1:])
        elif cmd == "go":
            if worker and worker.is_alive():
                continue
            params = {}
            i = 1
            while i < len(tokens):
                t = tokens[i]
                if t in ("wtime", "btime", "winc", "binc", "movestogo", "depth", "movetime", "nodes"):
                    params[t] = int(tokens[i + 1])
                    i += 2
                else:
                    i += 1
            max_depth, time_limit = compute_limits(board_holder[0], params)
            worker = threading.Thread(
                target=run_search, args=(board_holder[0].copy(), max_depth, time_limit), daemon=True)
            worker.start()
        elif cmd == "stop":
            searcher.stop()
        elif cmd == "quit":
            searcher.stop()
            break
        # setoption and unknown commands are ignored

    if worker and worker.is_alive():
        worker.join(timeout=2)


if __name__ == "__main__":
    main()
