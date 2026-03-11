import re
import chess
import chess.variant
from Utils.i18n import t

name_conversion = {
    "queen": "q",
    "knight": "n",
    "rook": "r",
    "bishop": "b",
    "pawn": "p",
    "king": "k",
}


## a mirrored chessboard that sync with actual web view chessboard
class ChessBoard():
    def __init__(self, fen=None):
        self.board_object = chess.Board() if(fen==None) else chess.Board(fen)
        print(self.board_object)
        print()


    def moveByUCI(self, uciString):
        """
        This function make move by using UCI string [target, destination]\n
        Parameters :
            - uciString

        Returns:
            success:
                -turple(true, Board object)
            fails:
                -turple(false, Error type)
        """
        try:
            move = chess.Move.from_uci(uciString)
            sanString = self.board_object.san(move)
            self.board_object.push_uci(uciString)
            print("UCI move: ", uciString, sanString)
            return (uciString.upper(), sanString.upper())
        except Exception as e:
            return e

    def moveBySan(self, sanString):
        """
        This function make move by using SAN string\n
        Parameters :
            - sanString

        Returns:
            success:
                -turple(true, Board object)
            fails:
                -turple(false, Error type)
        """
        try:
            if sanString == "oo" or sanString == "00":
                sanString = "O-O"
            elif sanString == "ooo" or sanString == "000":
                sanString = "O-O-O"
            if "=" in sanString:
                idx = sanString.index("=")
                if idx + 1 < len(sanString):
                    sanString = (
                        sanString[: idx + 1]
                        + sanString[idx + 1].upper()
                        + sanString[idx + 2 :]
                    )
            if sanString and sanString[0] in {"k", "q", "r", "b", "n"}:
                sanString = sanString[0].upper() + sanString[1:]

            uciString = self.board_object.parse_san(sanString).uci()

            move = chess.Move.from_uci(uciString)
            standard_san_string = self.board_object.san(move)

            self.board_object.push_san(standard_san_string)
            print("SAN move", uciString, standard_san_string)
            return (uciString.upper(), standard_san_string.upper())
        except Exception as e:
            return e

    def moveWithValidate(self, moveString):
        ## make move first -> user confirm = no change -> user cancel = back
        moveString = moveString.lower()
        moveString = re.sub(r"\s+", "", moveString)
        moveString = moveString.replace("null", "")
        moveString = moveString.replace("to", "")
        moveString = moveString.replace("-", "")
        moveString = moveString.replace("0", "o")

        print(f"move with validate, moveString = {moveString}")
        # ===== 先嘗試以座標形式 (UCI) 判斷，並給出更具體的錯誤原因 =====
        if len(moveString) >= 4:
            src = moveString[:2]
            dest = moveString[2:4]

            # 1) 格子名稱合法性
            if src not in chess.SQUARE_NAMES or dest not in chess.SQUARE_NAMES:
                return t("chess.invalid_square")

            # 2) 起點是否有棋子
            src_piece = self.check_grid(src)
            if isinstance(src_piece, str):
                # check_grid 可能已返回「無效格子名稱」
                return src_piece
            if src_piece is None:
                return t("chess.no_piece_on_source")

            # 3) 是否輪到該顏色行棋
            if src_piece.color != self.board_object.turn:
                # 當前輪到 self.board_object.turn 行棋，但起點是對手棋
                return t("chess.opponent_piece_on_source")

            # 4) 嘗試建立並檢查此步是否在合法走法列表中
            try:
                trial_move = chess.Move.from_uci(src + dest + moveString[4:])
            except Exception:
                trial_move = None

            if trial_move is not None and trial_move not in self.board_object.legal_moves:
                # 這裡再細分一個常見情況：兵升變
                if (
                    moveString.endswith(("8", "1"))
                    and src_piece.symbol().lower() == "p"
                ):
                    return t("chess.promotion")
                return t("chess.illegal_move")

        # 原本的 UCI 嘗試作為 fallback（例如帶有升變字元的完整 UCI）
        uciTrial = self.moveByUCI(moveString)
        print("uci Trial trial: ", moveString, " ", uciTrial)
        if not isinstance(uciTrial, Exception):
            return uciTrial
        elif isinstance(uciTrial, chess.IllegalMoveError):
            print(self.check_grid(moveString[:2]).__str__().lower())
            if (
                moveString.endswith("8") or moveString.endswith("1")
            ) and self.check_grid(moveString[:2]).__str__().lower() == "p":
                return t("chess.promotion")
            return t("chess.illegal_move")

        ##check SAN
        sanTrial = self.moveBySan(moveString)
        print("San Trial trial: ", moveString, " ", sanTrial)
        if not isinstance(sanTrial, Exception):
            return sanTrial

        ##check SAN with capitalized
        capSanTrial = self.moveBySan(moveString.capitalize())
        print("cap San Trial trial: ", moveString, " ", capSanTrial)
        if not isinstance(capSanTrial, Exception):
            return capSanTrial
        elif isinstance(capSanTrial, chess.IllegalMoveError):
            return t("chess.illegal_move")

        return t("chess.invalid_move")

    ##check piece type by square name
    def check_grid(self, grid):
        grid = grid.lower()
        try:
            piece = self.board_object.piece_at(chess.SQUARE_NAMES.index(grid))
        except Exception as e:
            return t("chess.invalid_square")
        return piece

    ##check the locations by piece type
    def check_piece(self, piece):
        target_piece = piece.lower()
        if len(piece) > 1:
            target_piece = name_conversion.get(piece.lower())
        white_list = []
        black_list = []
        for square in chess.SQUARE_NAMES:
            result_piece = self.check_grid(square)
            if (
                not result_piece == None
                and result_piece.symbol().lower() == target_piece
            ):
                if result_piece.symbol().islower():
                    black_list.append(square)
                else:
                    white_list.append(square)

        return {"WHITE": white_list, "BLACK": black_list}

    ##detect whether game end
    def detect_win(self):
        if self.board_object.is_checkmate():
            if self.board_object.turn:
                return t("chess.win.black_checkmate")
            else:
                return t("chess.win.white_checkmate")
        elif self.board_object.is_stalemate():
            return t("chess.win.stalemate")
        elif self.board_object.is_insufficient_material():
            return t("chess.win.insufficient_material")
        else:
            return t("chess.win.none")
        
    def current_board(self):
        return self.board_object.fen()
    
    def parseSquare(self, pos):
        return chess.parse_square(pos)