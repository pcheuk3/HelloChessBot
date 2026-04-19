import sys
import os
import chess
from threading import Event
from functools import partial
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QLabel,
    QPushButton,
    QLineEdit,
    QDialogButtonBox,
    QDialog,
    QMainWindow,
    QApplication,
    QHBoxLayout,
    QMessageBox,
    QCheckBox,
    QTextEdit,
    QSlider,
    QComboBox,
    QScrollArea,
    QFrame,
    QButtonGroup,
)
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from PyQt6.QtCore import QUrl, Qt, QTimer, QThread, pyqtSignal, QSettings
from PyQt6.QtGui import QFont, QShortcut, QKeySequence, QIcon


import Components.js_function as js_function    ## header file
from Components.piece_move_component import widgetDragDrop, widgetClick
from Components.chess_validation_component import ChessBoard
from Components.speak_component import TTSThread
from Utils.enum_helper import (
    Input_mode,
    Bot_flow_status,
    Game_flow_status,
    Speak_template,
    Game_play_mode,
    determinant,
    coach, adaptive, beginner, intermediate, advanced, master, athletes, musicians, creators, top_players, personalities, engine,
    timeControl,
    chatbot_response,
)
from Utils.i18n import t

import time


class RightWidget(QWidget):

    def __init__(self):
        super().__init__()
        global internal_speak_engine

        self.chatbot_button = QPushButton(t("ui.chatbot.button"))
        self.chatbot_button.setAccessibleDescription(t("ui.chatbot.desc"))

        #login components
        self.loginButton = QPushButton(t("ui.login.button"))
        self.loginButton.setAccessibleDescription(t("ui.login.desc"))
        
        self.logoutButton = QPushButton(t("ui.logout.button"))
        self.logoutButton.setAccessibleDescription(t("ui.logout.desc"))
        self.logoutButton.hide()  # Hidden by default until user logs in

        self.loginAccount_Input = QLineEdit()
        self.loginAccount_Input.setPlaceholderText(t("ui.login.username_placeholder"))
        self.loginAccount_Input.setAccessibleDescription(t("ui.login.username_desc"))

        self.loginPassword_Input = QLineEdit()
        self.loginPassword_Input.setPlaceholderText(t("ui.login.password_placeholder"))
        self.loginPassword_Input.setAccessibleDescription(t("ui.login.password_desc"))
        self.loginPassword_Input.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.login_button = QPushButton(t("ui.login.submit_button"))
        self.login_button.setAccessibleDescription(t("ui.login.submit_desc"))
        self.login_button.setAutoDefault(True)

        self.settingButton = QPushButton(t("ui.setting.button"))
        self.settingButton.setAccessibleDescription(t("ui.setting.desc"))

        #Computer mode components
        self.playWithComputerButton = QPushButton(t("ui.play.computer.button"))
        self.playWithComputerButton.setText(t("ui.play.computer.name"))
        self.playWithComputerButton.setAccessibleName(t("ui.play.computer.name"))
        self.playWithComputerButton.setAccessibleDescription(
            t("ui.play.computer.desc")
        )

        
        self.playWithComputerButton_Coach = QPushButton("Coach")
        self.playWithComputerButton_Adaptive = QPushButton("Adaptive")
        self.playWithComputerButton_Beginner = QPushButton("Beginner")
        self.playWithComputerButton_Intermediate = QPushButton("Intermediate")
        self.playWithComputerButton_Advanced = QPushButton("Advanced")
        self.playWithComputerButton_Master = QPushButton("Master")
        self.playWithComputerButton_Athletes = QPushButton("Athletes")
        self.playWithComputerButton_Musicians = QPushButton("Musicians")
        self.playWithComputerButton_Creators = QPushButton("Creators")
        self.playWithComputerButton_TopPlayers = QPushButton("Top Players")
        self.playWithComputerButton_Personalities = QPushButton("Personalities")
        self.playWithComputerButton_Engine = QPushButton("Engine")
        self.bot_category_buttons_map = {
            "coach": self.playWithComputerButton_Coach,
            "adaptive": self.playWithComputerButton_Adaptive,
            "beginner": self.playWithComputerButton_Beginner,
            "intermediate": self.playWithComputerButton_Intermediate,
            "advanced": self.playWithComputerButton_Advanced,
            "master": self.playWithComputerButton_Master,
            "athletes": self.playWithComputerButton_Athletes,
            "musicians": self.playWithComputerButton_Musicians,
            "creators": self.playWithComputerButton_Creators,
            "top_players": self.playWithComputerButton_TopPlayers,
            "personalities": self.playWithComputerButton_Personalities,
            "engine": self.playWithComputerButton_Engine,
        }

        self.bot_category_group = QButtonGroup(self)
        self.bot_category_group.setExclusive(True)
        for btn in self.bot_category_buttons_map.values():
            btn.setCheckable(True)
            self.bot_category_group.addButton(btn)

        self.bot_category_hint_label = QLabel(t("ui.play.computer.category_hint"))
        self.bot_category_hint_label.setWordWrap(True)

        self.play_button = QPushButton("Play")
        self.play_button.setAutoDefault(True)

        self.back_to_category_button = QPushButton("Back to Category")
        self.back_to_category_button.setAutoDefault(True)

        self.bot_list_hint_label = QLabel(t("ui.play.computer.category_hint"))
        self.bot_list_hint_label.setWordWrap(True)

        # Bot lists are shown as individual buttons instead of comboboxes
        self.bot_category_lists = {}
        self.bot_category_buttons = {}
        self.bot_buttons_all = []
        self.bot_buttons_group = QButtonGroup(self)
        self.bot_buttons_group.setExclusive(True)

        def create_bot_button(name: str, rating: str, category_key: str, level: int | None = None):
            label = f"{name} ({rating})"
            btn = QPushButton(label)
            btn.setAccessibleDescription(f"{name}\nRating: {rating}")
            btn.setCheckable(True)
            btn.setProperty("bot_name", name)
            btn.setProperty("bot_category", category_key)
            if level is not None:
                btn.setProperty("bot_level", level)
            self.bot_buttons_all.append(btn)
            self.bot_buttons_group.addButton(btn)
            self.bot_category_buttons.setdefault(category_key, []).append(btn)
            return btn

        def build_bot_list(category_key: str, items):
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            for item in items:
                value = item.value
                name = value.get("name", "")
                rating = value.get("rating", "")
                level = value.get("level")
                btn = create_bot_button(name, rating, category_key, level)
                layout.addWidget(btn)
            scroll = QScrollArea()
            scroll.setWidget(container)
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.hide()
            self.bot_category_lists[category_key] = scroll
            return scroll

        build_bot_list("coach", coach)
        build_bot_list("adaptive", adaptive)
        build_bot_list("beginner", beginner)
        build_bot_list("intermediate", intermediate)
        build_bot_list("advanced", advanced)
        build_bot_list("master", master)
        build_bot_list("athletes", athletes)
        build_bot_list("musicians", musicians)
        build_bot_list("creators", creators)
        build_bot_list("top_players", top_players)
        build_bot_list("personalities", personalities)
        build_bot_list("engine", engine)

        #Online mode components
        self.playWithOtherButton = QPushButton(t("ui.play.other.button"))
        self.playWithOtherButton.setAccessibleName(t("ui.play.other.name"))
        self.playWithOtherButton.setAccessibleDescription(
            t("ui.play.other.desc")
        )

        # first page: time control category buttons
        self.online_category_buttons = {
            "Bullet": QPushButton("Bullet"),
            "Blitz": QPushButton("Blitz"),
            "Rapid": QPushButton("Rapid"),
            "Daily": QPushButton("Daily"),
        }
        self.online_category_group = QButtonGroup(self)
        self.online_category_group.setExclusive(True)
        for btn in self.online_category_buttons.values():
            btn.setCheckable(True)
            self.online_category_group.addButton(btn)

        # second page: specific time control options buttons
        self.online_selection_buttons = []
        self.online_selection_group = QButtonGroup(self)
        self.online_selection_group.setExclusive(True)
        for _ in range(6):
            btn = QPushButton("")
            btn.setCheckable(True)
            btn.hide()
            self.online_selection_buttons.append(btn)
            self.online_selection_group.addButton(btn)

        # second page: confirm and start game and return to previous page buttons
        self.online_start_game_button = QPushButton("OK")
        self.online_start_game_button.setAutoDefault(True)

        self.back_to_previous_page_button = QPushButton("Back to Previous Page")
        self.back_to_previous_page_button.setAutoDefault(True)

        #Puzzle mode components
        self.puzzleModeButton = QPushButton(t("ui.puzzle.mode.button"))
        self.puzzleModeButton.setAccessibleDescription(t("ui.puzzle.mode.desc"))
        self.nextPuzzleButton = QPushButton(t("ui.puzzle.next.button"))
        self.retryPuzzleButton = QPushButton(t("ui.puzzle.retry.button"))

        #Game end components
        self.newgameButton = QPushButton(t("ui.game.new.button"))
        self.gamereviewButton = QPushButton(t("ui.game.review.button"))
        self.returnToHomePageButton = QPushButton(t("ui.game.return_home.button"))
        self.returnToHomePageButton.setAccessibleDescription(t("ui.game.return_home.desc"))
        self.returnToHomePageButton.setAutoDefault(True)

        #Analysis mode components
        self.analysisCurrentMove = QLabel()
        self.analysisCurrentMove.setText(t("ui.analysis.current_move"))
        self.analysisCurrentMove.setWordWrap(True)

        self.analysisComment = QLabel()
        self.analysisComment.setText(t("ui.analysis.comment"))
        self.analysisComment.setWordWrap(True)

        self.analysisExplanation = QLabel()
        self.analysisExplanation.setText(t("ui.analysis.explanation"))
        self.analysisExplanation.setWordWrap(True)

        self.analysis_NextMove_Button = QPushButton(t("ui.analysis.next_move"))
        self.analysis_PreviousMove_Button = QPushButton(t("ui.analysis.previous_move"))
        self.analysis_FirstMove_Button = QPushButton(t("ui.analysis.first_move"))
        # self.analysis_Explanation_Button = QPushButton("Explanation")
        self.analysis_BestMove_Button = QPushButton(t("ui.analysis.best_move"))
        # self.analysis_CurrentMove_Button = QPushButton("Current Move")        
        # self.analysis_LastMove_Button = QPushButton("Last Move")

        self.moveList = QLabel()
        self.moveList.setText(t("ui.move_list"))
        self.moveList.setWordWrap(True)  # allow move list to wrap
        self.moveList.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.whitePieces = QLabel()
        self.whitePieces.setText(t("ui.white_pieces"))
        self.whitePieces.setWordWrap(True)  # allow white pieces list to wrap
        self.whitePieces.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.blackPieces = QLabel()
        self.blackPieces.setText(t("ui.black_pieces"))
        self.blackPieces.setWordWrap(True)  # allow black pieces list to wrap
        self.blackPieces.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.colorBox = QLabel()
        self.colorBox.setText(t("ui.assigned_color"))
        self.colorBox.setWordWrap(True)  # allow color information to wrap
        self.colorBox.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.opponentBox = QLabel()
        self.opponentBox.setText(t("ui.opponent_last_move"))
        self.opponentBox.setWordWrap(True)  # allow opponent move information to wrap
        self.opponentBox.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.check_time = QPushButton(t("ui.check_time.button"))
        self.check_time.setAutoDefault(True)

        # current game analysis button (only visible in game, trigger analysis when pressed)
        self.currentGameAnalysisButton = QPushButton(t("ui.current_game_analysis.button"))
        self.currentGameAnalysisButton.setAccessibleDescription(t("ui.current_game_analysis.desc"))
        self.currentGameAnalysisButton.setAutoDefault(True)

        self.undo_button = QPushButton(t("ui.undo.button"))
        self.undo_button.setAutoDefault(True)

        self.resign = QPushButton(t("ui.resign.button"))
        self.resign.setAutoDefault(True)

        self.check_position = QLineEdit()
        self.check_position.setPlaceholderText(t("ui.check_position.placeholder"))
        self.check_position.setAccessibleName(t("ui.check_position.name"))
        self.check_position.setAccessibleDescription(
            t("ui.check_position.desc")
        )

        self.check_being_attacked = QPushButton(t("ui.macro_view.button"))
        self.check_being_attacked.setAutoDefault(True)

        self.commandPanel = QLineEdit()
        self.commandPanel.setPlaceholderText(t("ui.command_panel.placeholder"))
        self.commandPanel.setAccessibleName(t("ui.command_panel.name"))
        self.commandPanel.setAccessibleDescription(t("ui.command_panel.desc"))
        
        self.selectPanel = QLineEdit()
        self.selectPanel.setPlaceholderText(t("ui.select_panel.placeholder"))

        self.currentGameAnalysisButton.setText(t("ui.current_game_analysis.button"))
        self.currentGameAnalysisButton.setAccessibleDescription(t("ui.current_game_analysis.desc"))
        self.check_being_attacked.setText(t("ui.macro_view.button"))
        self.play_button.setText(t("ui.common.play"))
        self.back_to_category_button.setText(t("ui.common.back_to_category"))
        self.online_start_game_button.setText(t("ui.common.ok"))
        self.back_to_previous_page_button.setText(t("ui.common.back_to_previous_page"))

        self.play_button.setText(t("ui.common.play"))
        self.back_to_category_button.setText(t("ui.common.back_to_category"))
        self.online_start_game_button.setText(t("ui.common.ok"))
        self.back_to_previous_page_button.setText(t("ui.common.back_to_previous_page"))

        # update embedded Chatbot window language
        if hasattr(self, "chatbotWidget") and self.chatbotWidget:
            self.chatbotWidget.retranslate_ui()

       
        font = QFont()
        font.setPointSize(18)
        self.commandPanel.setFont(font)
        self.check_position.setFont(font)

        smallfont = QFont()
        smallfont.setPointSize(18)
        self.moveList.setFont(smallfont)

        # allow long text (like move list / white pieces) to scroll vertically
        self.whitePiecesScroll = QScrollArea()
        self.whitePiecesScroll.setWidget(self.whitePieces)
        self.whitePiecesScroll.setWidgetResizable(True)
        self.whitePiecesScroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.whitePiecesScroll.setFrameShape(QFrame.Shape.NoFrame)

        self.blackPiecesScroll = QScrollArea()
        self.blackPiecesScroll.setWidget(self.blackPieces)
        self.blackPiecesScroll.setWidgetResizable(True)
        self.blackPiecesScroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.blackPiecesScroll.setFrameShape(QFrame.Shape.NoFrame)

        self.moveListScroll = QScrollArea()
        self.moveListScroll.setWidget(self.moveList)
        self.moveListScroll.setWidgetResizable(True)
        self.moveListScroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.moveListScroll.setFrameShape(QFrame.Shape.NoFrame)

        self.opponentBoxScroll = QScrollArea()
        self.opponentBoxScroll.setWidget(self.opponentBox)
        self.opponentBoxScroll.setWidgetResizable(True)
        self.opponentBoxScroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.opponentBoxScroll.setFrameShape(QFrame.Shape.NoFrame)

        self.login_menu = []
        self.login_menu.append(self.loginAccount_Input)
        self.login_menu.append(self.loginPassword_Input)
        self.login_menu.append(self.login_button)

        self.setting_menu = []
        self.setting_menu.append(self.loginButton)
        self.setting_menu.append(self.logoutButton)
        self.setting_menu.append(self.playWithComputerButton)
        self.setting_menu.append(self.playWithOtherButton)
        self.setting_menu.append(self.puzzleModeButton)
        self.setting_menu.append(self.chatbot_button)
        self.play_menu = []
        # use scrollable container to wrap long text content
        self.play_menu.append(self.whitePiecesScroll)
        self.play_menu.append(self.blackPiecesScroll)
        self.play_menu.append(self.colorBox)
        self.play_menu.append(self.moveListScroll)
        self.play_menu.append(self.opponentBoxScroll)
        self.play_menu.append(self.undo_button)
        self.play_menu.append(self.resign)
        self.play_menu.append(self.check_time)
        self.play_menu.append(self.currentGameAnalysisButton)
        self.play_menu.append(self.check_being_attacked)
        self.play_menu.append(self.check_position)
        self.play_menu.append(self.commandPanel)
        # add Return Home Page button below Setting button in game playing interface
        self.play_menu.append(self.returnToHomePageButton)

        # online battle menu: contains category buttons on first page and time control buttons on second page
        self.online_mode_select_menu = []
        # first page category
        for btn in self.online_category_buttons.values():
            self.online_mode_select_menu.append(btn)
        # second page specific time control options
        for btn in self.online_selection_buttons:
            self.online_mode_select_menu.append(btn)
        # second page function buttons
        self.online_mode_select_menu.append(self.online_start_game_button)
        self.online_mode_select_menu.append(self.back_to_previous_page_button)

        self.bot_category_select_menu = []
        self.bot_category_select_menu.append(self.playWithComputerButton_Coach)
        self.bot_category_select_menu.append(self.playWithComputerButton_Adaptive)
        self.bot_category_select_menu.append(self.playWithComputerButton_Beginner)
        self.bot_category_select_menu.append(self.playWithComputerButton_Intermediate)
        self.bot_category_select_menu.append(self.playWithComputerButton_Advanced)
        self.bot_category_select_menu.append(self.playWithComputerButton_Master)
        self.bot_category_select_menu.append(self.playWithComputerButton_Athletes)
        self.bot_category_select_menu.append(self.playWithComputerButton_Musicians)
        self.bot_category_select_menu.append(self.playWithComputerButton_Creators)
        self.bot_category_select_menu.append(self.playWithComputerButton_TopPlayers)
        self.bot_category_select_menu.append(self.playWithComputerButton_Personalities)
        self.bot_category_select_menu.append(self.playWithComputerButton_Engine)

        self.bot_combobox = []
        # use per-category scroll lists with buttons instead of comboboxes
        self.bot_category_lists = getattr(self, "bot_category_lists", {})

        self.game_end_menu = []
        self.game_end_menu.append(self.newgameButton)
        self.game_end_menu.append(self.gamereviewButton)

        self.puzzle_end_menu = []
        self.puzzle_end_menu.append(self.nextPuzzleButton)
        self.puzzle_end_menu.append(self.retryPuzzleButton)

        self.analysis_menu = []
        self.analysis_menu.append(self.analysisCurrentMove)
        self.analysis_menu.append(self.analysisComment)
        self.analysis_menu.append(self.analysisExplanation)
        self.analysis_menu.append(self.analysis_PreviousMove_Button)
        self.analysis_menu.append(self.analysis_NextMove_Button)
        self.analysis_menu.append(self.analysis_FirstMove_Button)
        # self.analysis_menu.append(self.analysis_LastMove_Button)
        # self.analysis_menu.append(self.analysis_Explanation_Button)
        self.analysis_menu.append(self.analysis_BestMove_Button)
        # self.analysis_menu.append(self.analysis_CurrentMove_Button)

        #analysis control button
        self.analysisButton = []
        self.analysisButton.append(self.analysis_PreviousMove_Button)
        self.analysisButton.append(self.analysis_NextMove_Button)
        self.analysisButton.append(self.analysis_FirstMove_Button)
        # self.analysisButton.append(self.analysis_LastMove_Button)
        # self.analysisButton.append(self.analysis_Explanation_Button)
        self.analysisButton.append(self.analysis_BestMove_Button)
        # self.analysisButton.append(self.analysis_CurrentMove_Button)

        self.setting_layout = QVBoxLayout()

        for item in self.analysisButton:
            item.setAutoDefault(True)
            
        for item in self.setting_menu:
            self.setting_layout.addWidget(item)
            item.setAutoDefault(True)

        for item in self.login_menu:
            self.setting_layout.addWidget(item)
            item.hide()

        self.login_menu.append(self.returnToHomePageButton)

        for item in self.play_menu:
            self.setting_layout.addWidget(item)
            item.hide()

        for item in self.online_mode_select_menu:
            self.setting_layout.addWidget(item)
            item.setAutoDefault(True)
            item.hide()
        
        self.online_mode_select_menu.append(self.returnToHomePageButton)

        for item in self.bot_category_select_menu:
            self.setting_layout.addWidget(item)
            item.setAutoDefault(True)
            item.hide()

        self.setting_layout.addWidget(self.bot_category_hint_label)
        self.bot_category_hint_label.hide()
        self.bot_category_select_menu.append(self.bot_category_hint_label)

        self.bot_category_select_menu.append(self.returnToHomePageButton)        

        for item in self.bot_combobox:
            self.setting_layout.addWidget(item)
            item.hide()

        # add per-category bot lists (scrollable) to layout
        for key, scroll in self.bot_category_lists.items():
            self.setting_layout.addWidget(scroll)
            scroll.hide()

        self.setting_layout.addWidget(self.play_button)
        self.play_button.hide()
        self.setting_layout.addWidget(self.back_to_category_button)
        self.back_to_category_button.hide()

        self.setting_layout.addWidget(self.bot_list_hint_label)
        self.bot_list_hint_label.hide()

        for item in self.game_end_menu:
            self.setting_layout.addWidget(item)
            item.setAutoDefault(True)
            item.hide()

        self.game_end_menu.append(self.returnToHomePageButton)

        for item in self.puzzle_end_menu:
            self.setting_layout.addWidget(item)
            item.setAutoDefault(True)
            item.hide()

        self.puzzle_end_menu.append(self.returnToHomePageButton)

        for item in self.analysis_menu:
            self.setting_layout.addWidget(item)
            item.hide()

        self.analysis_menu.append(self.returnToHomePageButton)


        self.setting_layout.addWidget(self.settingButton) #setting button
        self.setting_menu.append(self.settingButton)
        self.online_mode_select_menu.append(self.settingButton)
        self.play_menu.append(self.settingButton)
        self.analysis_menu.append(self.settingButton)
        
        self.setting_layout.addWidget(self.returnToHomePageButton)
        self.returnToHomePageButton.hide()
        
        self.settingButton.setAutoDefault(True)
        self.settingButton.show()

        self.setLayout(self.setting_layout)

    def retranslate_ui(self):

        self.chatbot_button.setText(t("ui.chatbot.button"))
        self.chatbot_button.setAccessibleDescription(t("ui.chatbot.desc"))

        self.loginButton.setText(t("ui.login.button"))
        self.loginButton.setAccessibleDescription(t("ui.login.desc"))

        self.logoutButton.setText(t("ui.logout.button"))
        self.logoutButton.setAccessibleDescription(t("ui.logout.desc"))

        self.loginAccount_Input.setPlaceholderText(t("ui.login.username_placeholder"))
        self.loginAccount_Input.setAccessibleDescription(t("ui.login.username_desc"))

        self.loginPassword_Input.setPlaceholderText(t("ui.login.password_placeholder"))
        self.loginPassword_Input.setAccessibleDescription(t("ui.login.password_desc"))

        self.login_button.setText(t("ui.login.submit_button"))
        self.login_button.setAccessibleDescription(t("ui.login.submit_desc"))

        self.settingButton.setText(t("ui.setting.button"))
        self.settingButton.setAccessibleDescription(t("ui.setting.desc"))

        self.playWithComputerButton.setText(t("ui.play.computer.button"))
        self.playWithComputerButton.setAccessibleName(t("ui.play.computer.name"))
        self.playWithComputerButton.setAccessibleDescription(t("ui.play.computer.desc"))

        self.bot_category_hint_label.setText(t("ui.play.computer.category_hint"))

        self.playWithOtherButton.setText(t("ui.play.other.button"))
        self.playWithOtherButton.setAccessibleName(t("ui.play.other.name"))
        self.playWithOtherButton.setAccessibleDescription(t("ui.play.other.desc"))

        self.bot_list_hint_label.setText(t("ui.play.computer.category_hint"))

        self.puzzleModeButton.setText(t("ui.puzzle.mode.button"))
        self.puzzleModeButton.setAccessibleDescription(t("ui.puzzle.mode.desc"))
        self.nextPuzzleButton.setText(t("ui.puzzle.next.button"))
        self.retryPuzzleButton.setText(t("ui.puzzle.retry.button"))

        self.newgameButton.setText(t("ui.game.new.button"))
        self.gamereviewButton.setText(t("ui.game.review.button"))
        self.returnToHomePageButton.setText(t("ui.game.return_home.button"))
        self.returnToHomePageButton.setAccessibleDescription(t("ui.game.return_home.desc"))

        self.analysisCurrentMove.setText(t("ui.analysis.current_move"))
        self.analysisComment.setText(t("ui.analysis.comment"))
        self.analysisExplanation.setText(t("ui.analysis.explanation"))
        self.analysis_NextMove_Button.setText(t("ui.analysis.next_move"))
        self.analysis_PreviousMove_Button.setText(t("ui.analysis.previous_move"))
        self.analysis_FirstMove_Button.setText(t("ui.analysis.first_move"))
        self.analysis_BestMove_Button.setText(t("ui.analysis.best_move"))

        self.moveList.setText(t("ui.move_list"))
        self.whitePieces.setText(t("ui.white_pieces"))
        self.blackPieces.setText(t("ui.black_pieces"))
        self.colorBox.setText(t("ui.assigned_color"))
        self.opponentBox.setText(t("ui.opponent_last_move"))

        self.check_time.setText(t("ui.check_time.button"))
        self.currentGameAnalysisButton.setText(t("ui.current_game_analysis.button"))
        self.currentGameAnalysisButton.setAccessibleDescription(t("ui.current_game_analysis.desc"))
        self.check_being_attacked.setText(t("ui.macro_view.button"))
        self.undo_button.setText(t("ui.undo.button"))
        self.resign.setText(t("ui.resign.button"))

        self.check_position.setPlaceholderText(t("ui.check_position.placeholder"))
        self.check_position.setAccessibleName(t("ui.check_position.name"))
        self.check_position.setAccessibleDescription(t("ui.check_position.desc"))

        self.commandPanel.setPlaceholderText(t("ui.command_panel.placeholder"))
        self.commandPanel.setAccessibleName(t("ui.command_panel.name"))
        self.commandPanel.setAccessibleDescription(t("ui.command_panel.desc"))

        self.selectPanel.setPlaceholderText(t("ui.select_panel.placeholder"))

