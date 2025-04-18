from const import *
from square import Square
from piece import *
from move import Move
from sound import Sound
import copy
import os

class Board:

    def __init__(self):
        self.squares = [[0, 0, 0, 0, 0, 0, 0, 0] for col in range(COLS)]
        self.last_move = None
        self._create()
        self._add_pieces('white')
        self._add_pieces('black')

    def move(self, piece, move, testing=False):
        initial = move.initial
        final = move.final
        en_passant_empty = self.squares[final.row][final.col].isempty()

        self.squares[initial.row][initial.col].piece = None
        self.squares[final.row][final.col].piece = piece

        if isinstance(piece, Pawn):
            diff = final.col - initial.col
            if diff != 0 and en_passant_empty:
                self.squares[initial.row][initial.col + diff].piece = None
                if not testing:
                    Sound(os.path.join('assets/sounds/capture.wav')).play()
            else:
                self.check_promotion(piece, final)

        if isinstance(piece, King) and self.castling(initial, final) and not testing:
            diff = final.col - initial.col
            rook = piece.left_rook if diff < 0 else piece.right_rook
            self.move(rook, rook.moves[-1])

        piece.moved = True
        piece.clear_moves()
        self.last_move = move

    def valid_move(self, piece, move):
        return move in piece.moves

    def check_promotion(self, piece, final):
        if final.row == 0 or final.row == 7:
            self.squares[final.row][final.col].piece = Queen(piece.color)

    def castling(self, initial, final):
        return abs(initial.col - final.col) == 2

    def set_true_en_passant(self, piece):
        if not isinstance(piece, Pawn): return
        for row in range(ROWS):
            for col in range(COLS):
                if isinstance(self.squares[row][col].piece, Pawn):
                    self.squares[row][col].piece.en_passant = False
        piece.en_passant = True

    def in_check(self, piece, move):
        temp_piece = copy.deepcopy(piece)
        temp_board = copy.deepcopy(self)
        temp_board.move(temp_piece, move, testing=True)
        for row in range(ROWS):
            for col in range(COLS):
                if temp_board.squares[row][col].has_enemy_piece(piece.color):
                    p = temp_board.squares[row][col].piece
                    temp_board.calc_moves(p, row, col, bool=False)
                    for m in p.moves:
                        if isinstance(m.final.piece, King):
                            return True
        return False

    def calc_moves(self, piece, row, col, bool=True):
        def pawn_moves():
            steps = 1 if piece.moved else 2
            start = row + piece.dir
            end = row + piece.dir * (1 + steps)

            for r in range(start, end, piece.dir):
                if Square.in_range(r) and self.squares[r][col].isempty():
                    move = Move(Square(row, col), Square(r, col))
                    if not bool or not self.in_check(piece, move):
                        piece.add_move(move)
                else:
                    break

            for dc in [-1, 1]:
                r = row + piece.dir
                c = col + dc
                if Square.in_range(r, c) and self.squares[r][c].has_enemy_piece(piece.color):
                    move = Move(Square(row, col), Square(r, c, self.squares[r][c].piece))
                    if not bool or not self.in_check(piece, move):
                        piece.add_move(move)

            if row == (3 if piece.color == 'white' else 4):
                for dc in [-1, 1]:
                    c = col + dc
                    if Square.in_range(c):
                        p = self.squares[row][c].piece
                        if isinstance(p, Pawn) and p.en_passant:
                            fr = 2 if piece.color == 'white' else 5
                            move = Move(Square(row, col), Square(fr, c, p))
                            if not bool or not self.in_check(piece, move):
                                piece.add_move(move)

        def knight_moves():
            for dr, dc in [(-2, 1), (-1, 2), (1, 2), (2, 1),
                           (2, -1), (1, -2), (-1, -2), (-2, -1)]:
                r, c = row + dr, col + dc
                if Square.in_range(r, c) and self.squares[r][c].isempty_or_enemy(piece.color):
                    move = Move(Square(row, col), Square(r, c, self.squares[r][c].piece))
                    if not bool or not self.in_check(piece, move):
                        piece.add_move(move)

        def straightline_moves(incrs):
            for dr, dc in incrs:
                r, c = row + dr, col + dc
                while Square.in_range(r, c):
                    dest = self.squares[r][c]
                    move = Move(Square(row, col), Square(r, c, dest.piece))
                    if dest.isempty():
                        if not bool or not self.in_check(piece, move):
                            piece.add_move(move)
                    elif dest.has_enemy_piece(piece.color):
                        if not bool or not self.in_check(piece, move):
                            piece.add_move(move)
                        break
                    else:
                        break
                    r += dr
                    c += dc

        def king_moves():
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0: continue
                    r, c = row + dr, col + dc
                    if Square.in_range(r, c) and self.squares[r][c].isempty_or_enemy(piece.color):
                        move = Move(Square(row, col), Square(r, c))
                        if not bool or not self.in_check(piece, move):
                            piece.add_move(move)

            for side, rook_col, spaces, king_end_col, rook_end_col in [('left', 0, [1, 2, 3], 2, 3),
                                                                        ('right', 7, [5, 6], 6, 5)]:
                rook = self.squares[row][rook_col].piece
                if isinstance(rook, Rook) and not rook.moved and not piece.moved:
                    if all(not self.squares[row][c].has_piece() for c in spaces):
                        king_move = Move(Square(row, col), Square(row, king_end_col))
                        rook_move = Move(Square(row, rook_col), Square(row, rook_end_col))
                        if not bool or (not self.in_check(piece, king_move) and not self.in_check(rook, rook_move)):
                            piece.add_move(king_move)
                            rook.add_move(rook_move)
                            if side == 'left':
                                piece.left_rook = rook
                            else:
                                piece.right_rook = rook

        if isinstance(piece, Pawn): pawn_moves()
        elif isinstance(piece, Knight): knight_moves()
        elif isinstance(piece, Bishop): straightline_moves([(-1,1), (-1,-1), (1,1), (1,-1)])
        elif isinstance(piece, Rook): straightline_moves([(-1,0), (0,1), (1,0), (0,-1)])
        elif isinstance(piece, Queen): straightline_moves([(-1,1), (-1,-1), (1,1), (1,-1), (-1,0), (0,1), (1,0), (0,-1)])
        elif isinstance(piece, King): king_moves()

    def _create(self):
        for row in range(ROWS):
            for col in range(COLS):
                self.squares[row][col] = Square(row, col)

    def _add_pieces(self, color):
        row_pawn, row_other = (6, 7) if color == 'white' else (1, 0)
        for col in range(COLS):
            self.squares[row_pawn][col] = Square(row_pawn, col, Pawn(color))
        self.squares[row_other][1] = Square(row_other, 1, Knight(color))
        self.squares[row_other][6] = Square(row_other, 6, Knight(color))
        self.squares[row_other][2] = Square(row_other, 2, Bishop(color))
        self.squares[row_other][5] = Square(row_other, 5, Bishop(color))
        self.squares[row_other][0] = Square(row_other, 0, Rook(color))
        self.squares[row_other][7] = Square(row_other, 7, Rook(color))
        self.squares[row_other][3] = Square(row_other, 3, Queen(color))
        self.squares[row_other][4] = Square(row_other, 4, King(color))
