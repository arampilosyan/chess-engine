"""Search: negamax + alpha-beta, iterative deepening, quiescence search,
transposition table, null-move pruning, killer/history move ordering."""
import time
import chess
import chess.polyglot

from evaluate import evaluate_relative, PIECE_VALUES

MATE = 100000
INF = 10 ** 9
MAX_PLY = 64
EXACT, LOWER, UPPER = 0, 1, 2
MATE_BOUND = MATE - 1000


class TimeUp(Exception):
    pass


def _to_tt(score, ply):
    if score > MATE_BOUND:
        return score + ply
    if score < -MATE_BOUND:
        return score - ply
    return score


def _from_tt(score, ply):
    if score > MATE_BOUND:
        return score - ply
    if score < -MATE_BOUND:
        return score + ply
    return score


class Searcher:
    def __init__(self):
        self.tt = {}
        self.nodes = 0
        self.deadline = None
        self.stop_flag = False
        self.can_stop = False
        self.killers = [[None, None] for _ in range(MAX_PLY + 8)]
        self.history = {}

    # ---------------------------------------------------------------- utils
    def stop(self):
        self.stop_flag = True

    def _check_time(self):
        if self.nodes & 1023:
            return
        if self.stop_flag:
            raise TimeUp
        if self.can_stop and self.deadline is not None and time.time() >= self.deadline:
            raise TimeUp

    def _order(self, board, moves, tt_move, ply):
        killers = self.killers[ply]

        def score(m):
            if m == tt_move:
                return 10_000_000
            if board.is_capture(m):
                victim = board.piece_type_at(m.to_square) or chess.PAWN  # en passant
                attacker = board.piece_type_at(m.from_square)
                s = 1_000_000 + 10 * PIECE_VALUES[victim] - PIECE_VALUES[attacker] // 100
                if m.promotion:
                    s += PIECE_VALUES[m.promotion]
                return s
            if m.promotion:
                return 900_000 + PIECE_VALUES[m.promotion]
            if m == killers[0]:
                return 500_000
            if m == killers[1]:
                return 400_000
            return self.history.get((m.from_square, m.to_square), 0)

        return sorted(moves, key=score, reverse=True)

    # ----------------------------------------------------------- public API
    def search(self, board, max_depth=64, time_limit=None, info=None):
        """Return the best move (or None if there are no legal moves)."""
        board = board.copy(stack=True)
        legal = list(board.legal_moves)
        if not legal:
            return None
        self.nodes = 0
        self.stop_flag = False
        self.can_stop = False
        self.history = {}
        self.killers = [[None, None] for _ in range(MAX_PLY + 8)]
        start = time.time()
        self.deadline = start + time_limit if time_limit else None

        best = legal[0]
        for depth in range(1, max_depth + 1):
            self.can_stop = depth > 1
            try:
                score, move = self._root(board, depth)
            except TimeUp:
                break
            if move is not None:
                best = move
            if info:
                info(depth, score, self.nodes, time.time() - start, [best])
            if abs(score) > MATE_BOUND:
                break
            if self.deadline and time.time() >= self.deadline:
                break
        return best

    # ----------------------------------------------------------------- root
    def _root(self, board, depth):
        key = chess.polyglot.zobrist_hash(board)
        entry = self.tt.get(key)
        tt_move = entry[3] if entry else None
        moves = self._order(board, list(board.legal_moves), tt_move, 0)

        alpha, beta = -INF, INF
        best_score, best_move = -INF, None
        for m in moves:
            board.push(m)
            score = -self._negamax(board, depth - 1, -beta, -alpha, 1)
            board.pop()
            if score > best_score:
                best_score, best_move = score, m
            if score > alpha:
                alpha = score
        self.tt[key] = (depth, EXACT, _to_tt(best_score, 0), best_move)
        return best_score, best_move

    # -------------------------------------------------------------- negamax
    def _negamax(self, board, depth, alpha, beta, ply):
        self.nodes += 1
        self._check_time()

        if board.is_repetition(2) or board.halfmove_clock >= 100 or board.is_insufficient_material():
            return 0

        in_check = board.is_check()
        if in_check and ply < MAX_PLY - 8:
            depth += 1  # check extension
        if depth <= 0 or ply >= MAX_PLY:
            return self._quiesce(board, alpha, beta, ply)

        key = chess.polyglot.zobrist_hash(board)
        entry = self.tt.get(key)
        tt_move = None
        if entry:
            e_depth, flag, e_score, tt_move = entry
            if e_depth >= depth:
                e_score = _from_tt(e_score, ply)
                if flag == EXACT:
                    return e_score
                if flag == LOWER:
                    alpha = max(alpha, e_score)
                else:
                    beta = min(beta, e_score)
                if alpha >= beta:
                    return e_score

        # Null-move pruning (not in check, and side has non-pawn material)
        if (depth >= 3 and not in_check and beta < MATE_BOUND
                and board.occupied_co[board.turn] & ~(board.pawns | board.kings)):
            board.push(chess.Move.null())
            score = -self._negamax(board, depth - 3, -beta, -beta + 1, ply + 1)
            board.pop()
            if score >= beta:
                return beta

        moves = list(board.legal_moves)
        if not moves:
            return -(MATE - ply) if in_check else 0
        moves = self._order(board, moves, tt_move, ply)

        orig_alpha = alpha
        best, best_move = -INF, None
        for m in moves:
            is_capture = board.is_capture(m)
            board.push(m)
            score = -self._negamax(board, depth - 1, -beta, -alpha, ply + 1)
            board.pop()
            if score > best:
                best, best_move = score, m
            if score > alpha:
                alpha = score
            if alpha >= beta:
                if not is_capture and not m.promotion:
                    k = self.killers[ply]
                    if k[0] != m:
                        k[1], k[0] = k[0], m
                    hk = (m.from_square, m.to_square)
                    self.history[hk] = self.history.get(hk, 0) + depth * depth
                break

        if best <= orig_alpha:
            flag = UPPER
        elif best >= beta:
            flag = LOWER
        else:
            flag = EXACT
        if len(self.tt) > 1_000_000:
            self.tt.clear()
        self.tt[key] = (depth, flag, _to_tt(best, ply), best_move)
        return best

    # ----------------------------------------------------------- quiescence
    def _quiesce(self, board, alpha, beta, ply):
        self.nodes += 1
        self._check_time()

        in_check = board.is_check()
        if ply >= MAX_PLY + 4:
            return evaluate_relative(board)

        if in_check:
            moves = list(board.legal_moves)
            if not moves:
                return -(MATE - ply)
            best = -INF
        else:
            stand = evaluate_relative(board)
            if stand >= beta:
                return stand
            alpha = max(alpha, stand)
            best = stand
            moves = [m for m in board.legal_moves if board.is_capture(m) or m.promotion]

        for m in self._order(board, moves, None, min(ply, MAX_PLY)):
            board.push(m)
            score = -self._quiesce(board, -beta, -alpha, ply + 1)
            board.pop()
            if score > best:
                best = score
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break
        return best
