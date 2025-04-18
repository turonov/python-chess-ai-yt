import pygame
import sys
import chess.engine
import json
import time

from const import *
from game import Game
from square import Square
from move import Move
# from board import Board  # Removed to avoid circular import


class Main:

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH + 300, HEIGHT))
        pygame.display.set_caption('Chess')
        self.game = Game()

        STOCKFISH_PATH = "/usr/games/stockfish"
        self.engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)

        self.pgn_moves = []
        self.evaluation_log = []
        self.start_time = time.time()

    def best_move_suggestion(self, fen):
        try:
            board = chess.Board(fen)
            result = self.engine.analyse(board, chess.engine.Limit(time=0.2))
            best_move = result["pv"][0]
            move_str = board.san(best_move)
            return move_str
        except Exception as e:
            print("[XATOLIK] Eng yaxshi yurishni aniqlashda xato:", e)
            return "?"

    def mainloop(self):
        screen = self.screen
        game = self.game
        board = self.game.board
        dragger = self.game.dragger
        font = pygame.font.SysFont("Arial", 20)

        if game.next_player == 'black':
            self.play_ai_turn(board, game)

        while True:
            game.show_bg(screen)
            game.show_last_move(screen)
            game.show_moves(screen)
            game.show_pieces(screen)
            game.show_hover(screen)

            pygame.draw.rect(screen, (245, 245, 245), (WIDTH, 0, 300, HEIGHT))
            y_offset = 10
            for item in self.evaluation_log[-20:]:
                move_line = f"{item['move']}: {item['comment']}"
                suggestion_line = f"{item.get('suggestion', '')}"
                move_surface = font.render(move_line, True, (0, 0, 0))
                suggestion_surface = font.render(suggestion_line, True, (100, 100, 100))
                screen.blit(move_surface, (WIDTH + 10, y_offset))
                y_offset += 22
                screen.blit(suggestion_surface, (WIDTH + 20, y_offset))
                y_offset += 25

            if dragger.dragging:
                dragger.update_blit(screen)

            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    dragger.update_mouse(event.pos)
                    clicked_row = dragger.mouseY // SQSIZE
                    clicked_col = dragger.mouseX // SQSIZE
                    if 0 <= clicked_row < ROWS and 0 <= clicked_col < COLS:
                        if board.squares[clicked_row][clicked_col].has_piece():
                            piece = board.squares[clicked_row][clicked_col].piece
                            if piece.color == game.next_player:
                                board.calc_moves(piece, clicked_row, clicked_col, True)
                                dragger.save_initial(event.pos)
                                dragger.drag_piece(piece)
                                game.show_bg(screen)
                                game.show_last_move(screen)
                                game.show_moves(screen)
                                game.show_pieces(screen)

                elif event.type == pygame.MOUSEMOTION:
                    motion_row = event.pos[1] // SQSIZE
                    motion_col = event.pos[0] // SQSIZE
                    if 0 <= motion_row < ROWS and 0 <= motion_col < COLS:
                        game.set_hover(motion_row, motion_col)
                    if dragger.dragging:
                        dragger.update_mouse(event.pos)
                        game.show_bg(screen)
                        game.show_last_move(screen)
                        game.show_moves(screen)
                        game.show_pieces(screen)
                        game.show_hover(screen)
                        dragger.update_blit(screen)

                elif event.type == pygame.MOUSEBUTTONUP:
                    if dragger.dragging:
                        dragger.update_mouse(event.pos)
                        released_row = dragger.mouseY // SQSIZE
                        released_col = dragger.mouseX // SQSIZE

                        if 0 <= released_row < ROWS and 0 <= released_col < COLS:
                            initial = Square(dragger.initial_row, dragger.initial_col)
                            final = Square(released_row, released_col)
                            move = Move(initial, final)

                            if board.valid_move(dragger.piece, move):
                                start_time = time.time()
                                captured = board.squares[released_row][released_col].has_piece()
                                board.move(dragger.piece, move)
                                board.set_true_en_passant(dragger.piece)
                                game.play_sound(captured)
                                game.show_bg(screen)
                                game.show_last_move(screen)
                                game.show_pieces(screen)

                                fen_before = board_to_fen(board, 'w' if game.next_player == 'black' else 'b')
                                uci = f"{chr(initial.col + ord('a'))}{8 - initial.row}{chr(final.col + ord('a'))}{8 - final.row}"

                                try:
                                    user_board = chess.Board(fen_before)
                                    chess_move = chess.Move.from_uci(uci)

                                    if chess_move not in user_board.legal_moves:
                                        raise ValueError("Illegal move")

                                    pgn_move = user_board.san(chess_move)
                                    self.pgn_moves.append(pgn_move)

                                    eval_before = self.engine.analyse(user_board, chess.engine.Limit(depth=12))['score'].relative.score(mate_score=10000)
                                    user_board.push(chess_move)
                                    eval_after = self.engine.analyse(user_board, chess.engine.Limit(depth=12))['score'].relative.score(mate_score=10000)
                                    diff = (eval_after or 0) - (eval_before or 0)

                                    if diff >= 50:
                                        comment = "✅ Juda yaxshi yurish!"
                                    elif diff >= -20:
                                        comment = "ℹ️ Yaxshi, ammo mukammal emas."
                                    elif diff >= -100:
                                        comment = "⚠️ Zaif yurish."
                                    else:
                                        comment = "❌ Katta xatolik."

                                    duration = round(time.time() - start_time, 2)
                                    best = self.best_move_suggestion(fen_before)
                                    self.evaluation_log.append({"move": pgn_move, "comment": comment, "eval": eval_after, "time": duration, "suggestion": f"(Eng yaxshisi: {best})"})
                                    print(f"[PGN - Player] {pgn_move} | {comment} | Eval: {eval_after} | Time: {duration}s | Best: {best}")

                                    if user_board.is_checkmate():
                                        print("♛ Checkmate! O'yin tugadi.")

                                except Exception as e:
                                    print(f"[XATOLIK] {e}")

                                game.next_turn()

                                if game.next_player == 'black':
                                    self.play_ai_turn(board, game)

                    dragger.undrag_piece()

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_t:
                        game.change_theme()
                    if event.key == pygame.K_r:
                        game.reset()
                        game = self.game
                        board = self.game.board
                        dragger = self.game.dragger
                        self.pgn_moves = []
                        self.evaluation_log = []
                        self.start_time = time.time()
                        print("[INFO] O'yin qayta boshlandi")
                    if event.key == pygame.K_s:
                        with open("game.pgn", "w") as f:
                            f.write(" ".join(self.pgn_moves))
                        with open("evaluation.json", "w") as f:
                            json.dump(self.evaluation_log, f, indent=4)
                        print("[INFO] O'yin PGN va baholar saqlandi.")

                elif event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            pygame.display.update()

    def play_ai_turn(self, board, game):
        turn = 'b'
        fen = board_to_fen(board, turn)
        try:
            sf_board = chess.Board(fen)
            result = self.engine.play(sf_board, chess.engine.Limit(time=0.1))
            uci_move = result.move.uci()
            pgn_move = sf_board.san(result.move)
            self.pgn_moves.append(pgn_move)
            best_ai = self.best_move_suggestion(fen)
            self.evaluation_log.append({"move": pgn_move, "comment": f"♟️ AI yurdi ({uci_move})", "suggestion": f"(Tavsiyasi: {best_ai})"})

            start_col = ord(uci_move[0]) - ord('a')
            start_row = 8 - int(uci_move[1])
            end_col = ord(uci_move[2]) - ord('a')
            end_row = 8 - int(uci_move[3])

            ai_piece = board.squares[start_row][start_col].piece
            initial = Square(start_row, start_col)
            final = Square(end_row, end_col)
            ai_move = Move(initial, final)

            if board.valid_move(ai_piece, ai_move):
                board.move(ai_piece, ai_move)
                game.play_sound(False)
                game.show_bg(self.screen)
                game.show_last_move(self.screen)
                game.show_pieces(self.screen)
                game.next_turn()

                if sf_board.is_checkmate():
                    print("♚ AI bilan o'yinda Checkmate! O'yin tugadi.")

        except Exception as e:
            print("[ERROR] Stockfish yurishda xatolik:", e)


def board_to_fen(board, turn='w'):
    fen_rows = []
    for row in board.squares:
        empty_count = 0
        fen_row = ''
        for square in row:
            if square.piece is None:
                empty_count += 1
            else:
                if empty_count > 0:
                    fen_row += str(empty_count)
                    empty_count = 0
                piece = square.piece
                letter = piece.name[0]
                if piece.name == 'knight':
                    letter = 'n'
                if piece.name == 'pawn':
                    letter = 'p'
                fen_row += letter.upper() if piece.color == 'white' else letter.lower()
        if empty_count > 0:
            fen_row += str(empty_count)
        fen_rows.append(fen_row)

    fen = '/'.join(fen_rows) + f' {turn} - - 0 1'
    return fen


main = Main()
main.mainloop()
