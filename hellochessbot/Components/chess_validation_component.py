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
           
            if sanString and sanString[0] in {"k", "q", "r", "n"}:
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
        raw_move = "" if moveString is None else str(moveString)
        san_candidate = re.sub(r"\s+", "", raw_move)
        san_candidate = san_candidate.replace("null", "")

        
        uci_candidate = san_candidate.lower()
        uci_candidate = uci_candidate.replace("to", "")
        uci_candidate = uci_candidate.replace("-", "")
        uci_candidate = uci_candidate.replace("0", "o")

        print(f"move with validate, moveString = {uci_candidate}")
        
        if len(uci_candidate) >= 4:
            src = uci_candidate[:2]
            dest = uci_candidate[2:4]

            
            if src not in chess.SQUARE_NAMES or dest not in chess.SQUARE_NAMES:
                
                src = None
            else:
                
                src_piece = self.check_grid(src)
                if isinstance(src_piece, str):
                 
                    return src_piece
                if src_piece is None:
                    return t("chess.no_piece_on_source")

                if src_piece.color != self.board_object.turn:
                   
                    return t("chess.opponent_piece_on_source")

                
                try:
                    trial_move = chess.Move.from_uci(src + dest + uci_candidate[4:])
                except Exception:
                    trial_move = None

                if trial_move is not None and trial_move not in self.board_object.legal_moves:
                
                    if (
                        uci_candidate.endswith(("8", "1"))
                        and src_piece.symbol().lower() == "p"
                    ):
                        return t("chess.promotion")
                    return t("chess.illegal_move")

        
        uciTrial = self.moveByUCI(uci_candidate)
        print("uci Trial trial: ", uci_candidate, " ", uciTrial)
        if not isinstance(uciTrial, Exception):
            return uciTrial
        elif isinstance(uciTrial, chess.IllegalMoveError):
            print(self.check_grid(uci_candidate[:2]).__str__().lower())
            if (
                uci_candidate.endswith("8") or uci_candidate.endswith("1")
            ) and self.check_grid(uci_candidate[:2]).__str__().lower() == "p":
                return t("chess.promotion")
            return t("chess.illegal_move")

        ##check SAN
        sanTrial = self.moveBySan(san_candidate)
        print("San Trial trial: ", san_candidate, " ", sanTrial)
        if not isinstance(sanTrial, Exception):
            return sanTrial

        ##check SAN with capitalized
        capSanTrial = self.moveBySan(san_candidate.capitalize())
        print("cap San Trial trial: ", san_candidate, " ", capSanTrial)
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