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
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
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
    timeControlDeterminant_Type,
    timeControlDeterminant_Speak,
    chatbot_response,
)
from Utils.i18n import t

import pyaudio
import wave
import whisper
import torch

import time


class RightWidget(QWidget):
    """
    This class respresent the right widget.\n
    It contains command panel , query place.
    """

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

        # self.playWithComputerButton_BackToSchoolButton = QPushButton("Back To School")
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

        self.combobox_coach = QComboBox()
        self.combobox_coach.setAccessibleDescription("Coach Combobox")
        self.combobox_adaptive = QComboBox()
        self.combobox_adaptive.setAccessibleDescription("Adaptive Combobox")
        self.combobox_beginner = QComboBox()
        self.combobox_beginner.setAccessibleDescription("Beginner Combobox")
        self.combobox_intermediate = QComboBox()
        self.combobox_intermediate.setAccessibleDescription("Intermediate Combobox")
        self.combobox_advanced = QComboBox()
        self.combobox_advanced.setAccessibleDescription("Advanced Combobox")
        self.combobox_master = QComboBox()
        self.combobox_master.setAccessibleDescription("Master Combobox")
        self.combobox_athletes = QComboBox()
        self.combobox_athletes.setAccessibleDescription("Athletes Combobox")
        self.combobox_musicians = QComboBox()
        self.combobox_musicians.setAccessibleDescription("Musicians Combobox")
        self.combobox_creators = QComboBox()
        self.combobox_creators.setAccessibleDescription("Creators Combobox")
        self.combobox_top_players = QComboBox()
        self.combobox_top_players.setAccessibleDescription("Top Players Combobox")
        self.combobox_personalities = QComboBox()
        self.combobox_personalities.setAccessibleDescription("Personalities Combobox")
        self.combobox_engine = QComboBox()
        self.combobox_engine.setAccessibleDescription("Engine Combobox")

        self.play_button = QPushButton("Play")
        self.play_button.setAutoDefault(True)

        self.back_to_category_button = QPushButton("Back to Category")
        self.back_to_category_button.setAutoDefault(True)

        for item in coach:
            self.combobox_coach.addItem(item.value["name"])
            self.combobox_coach.setItemData(self.combobox_coach.count() - 1,
                                            f"{item.value['name']}\n Rating: {item.value['rating']}",
                                            Qt.ItemDataRole.AccessibleTextRole)
        for item in adaptive:
            self.combobox_adaptive.addItem(item.value["name"])
            self.combobox_adaptive.setItemData(self.combobox_adaptive.count() - 1,
                                            f"{item.value['name']}\n Rating: {item.value['rating']}",
                                            Qt.ItemDataRole.AccessibleTextRole)
        for item in beginner:
            self.combobox_beginner.addItem(item.value["name"])
            self.combobox_beginner.setItemData(self.combobox_beginner.count() - 1,
                                            f"{item.value['name']}\n Rating: {item.value['rating']}",
                                            Qt.ItemDataRole.AccessibleTextRole)
        for item in intermediate:
            self.combobox_intermediate.addItem(item.value["name"])
            self.combobox_intermediate.setItemData(self.combobox_intermediate.count() - 1,
                                            f"{item.value['name']}\n Rating: {item.value['rating']}",
                                            Qt.ItemDataRole.AccessibleTextRole)
        for item in advanced:
            self.combobox_advanced.addItem(item.value["name"])
            self.combobox_advanced.setItemData(self.combobox_advanced.count() - 1,
                                            f"{item.value['name']}\n Rating: {item.value['rating']}",
                                            Qt.ItemDataRole.AccessibleTextRole)
        for item in master:
            self.combobox_master.addItem(item.value["name"])
            self.combobox_master.setItemData(self.combobox_master.count() - 1,
                                            f"{item.value['name']}\n Rating: {item.value['rating']}",
                                            Qt.ItemDataRole.AccessibleTextRole)
        for item in athletes:
            self.combobox_athletes.addItem(item.value["name"])
            self.combobox_athletes.setItemData(self.combobox_athletes.count() - 1,
                                            f"{item.value['name']}\n Rating: {item.value['rating']}",
                                            Qt.ItemDataRole.AccessibleTextRole)
        for item in musicians:
            self.combobox_musicians.addItem(item.value["name"])
            self.combobox_musicians.setItemData(self.combobox_musicians.count() - 1,
                                            f"{item.value['name']}\n Rating: {item.value['rating']}",
                                            Qt.ItemDataRole.AccessibleTextRole)
        for item in creators:
            self.combobox_creators.addItem(item.value["name"])
            self.combobox_creators.setItemData(self.combobox_creators.count() - 1,
                                            f"{item.value['name']}\n Rating: {item.value['rating']}",
                                            Qt.ItemDataRole.AccessibleTextRole)
        for item in top_players:
            self.combobox_top_players.addItem(item.value["name"])
            self.combobox_top_players.setItemData(self.combobox_top_players.count() - 1,
                                            f"{item.value['name']}\n Rating: {item.value['rating']}",
                                            Qt.ItemDataRole.AccessibleTextRole)
        for item in personalities:
            self.combobox_personalities.addItem(item.value["name"])
            self.combobox_personalities.setItemData(self.combobox_personalities.count() - 1,
                                            f"{item.value['name']}\n Rating: {item.value['rating']}",
                                            Qt.ItemDataRole.AccessibleTextRole)
            
        for item in engine:
            self.combobox_engine.addItem(item.value["name"])
            self.combobox_engine.setItemData(self.combobox_engine.count() - 1,
                                            f"{item.value['name']}\n Rating: {item.value['rating']}",
                                                Qt.ItemDataRole.AccessibleTextRole)

        #Online mode components
        self.playWithOtherButton = QPushButton(t("ui.play.other.button"))
        self.playWithOtherButton.setAccessibleName(t("ui.play.other.name"))
        self.playWithOtherButton.setAccessibleDescription(
            t("ui.play.other.desc")
        )

        # 第一頁：時間控制大類按鈕
        self.online_category_buttons = {
            "Bullet": QPushButton("Bullet"),
            "Blitz": QPushButton("Blitz"),
            "Rapid": QPushButton("Rapid"),
            "Daily": QPushButton("Daily"),
        }

        # 第二頁：具體時間控制選項按鈕（最多 6 個，根據 txt 動態填入文字）
        self.online_selection_buttons = []
        for _ in range(6):
            btn = QPushButton("")
            btn.hide()
            self.online_selection_buttons.append(btn)

        # 第二頁：確認並開始遊戲與返回上一頁按鈕
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
        self.moveList.setWordWrap(True)  # 允許移動列表換行顯示
        # 讓 Tab 可以聚焦到這些資訊標籤，配合 main.py 的 handle_tab 自動朗讀內容
        self.moveList.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.whitePieces = QLabel()
        self.whitePieces.setText(t("ui.white_pieces"))
        self.whitePieces.setWordWrap(True)  # 允許白棋子列表換行顯示
        self.whitePieces.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.blackPieces = QLabel()
        self.blackPieces.setText(t("ui.black_pieces"))
        self.blackPieces.setWordWrap(True)  # 允許黑棋子列表換行顯示
        self.blackPieces.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.colorBox = QLabel()
        self.colorBox.setText(t("ui.assigned_color"))
        self.colorBox.setWordWrap(True)  # 允許顏色信息換行顯示
        self.colorBox.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.opponentBox = QLabel()
        self.opponentBox.setText(t("ui.opponent_last_move"))
        self.opponentBox.setWordWrap(True)  # 允許對手移動信息換行顯示
        self.opponentBox.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.check_time = QPushButton(t("ui.check_time.button"))
        self.check_time.setAutoDefault(True)

        # 目前局面分析按鈕（僅在遊戲中可見，按下才觸發分析）
        self.currentGameAnalysisButton = QPushButton("Current Game Analysis")
        self.currentGameAnalysisButton.setAccessibleDescription("Analyze current game situation")
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

        self.check_being_attacked = QPushButton("Macro View")
        self.check_being_attacked.setAutoDefault(True)

        self.commandPanel = QLineEdit()
        self.commandPanel.setPlaceholderText(t("ui.command_panel.placeholder"))
        self.commandPanel.setAccessibleName(t("ui.command_panel.name"))
        self.commandPanel.setAccessibleDescription(t("ui.command_panel.desc"))
        
        self.selectPanel = QLineEdit()
        self.selectPanel.setPlaceholderText(t("ui.select_panel.placeholder"))

        # 更新嵌入的 Chatbot 視窗語言
        if hasattr(self, "chatbotWidget") and self.chatbotWidget:
            self.chatbotWidget.retranslate_ui()

        # 更新嵌入的 ChatbotWindow 語言
        if hasattr(self, "chatbotWidget") and self.chatbotWidget:
            self.chatbotWidget.retranslate_ui()

        font = QFont()
        font.setPointSize(18)
        self.commandPanel.setFont(font)
        self.check_position.setFont(font)

        smallfont = QFont()
        smallfont.setPointSize(18)
        self.moveList.setFont(smallfont)

        # 讓長文字（如 move list / white pieces 等）可以垂直滾動顯示
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
        # 使用帶滾動條的容器包裹長文字內容
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
        # 在遊戲進行界面的 Setting 按鈕下方加入 Return Home Page 按鈕
        self.play_menu.append(self.returnToHomePageButton)

        # 在線對戰選單：包含第一頁的類別按鈕與第二頁的時間控制按鈕
        self.online_mode_select_menu = []
        # 第一頁類別
        for btn in self.online_category_buttons.values():
            self.online_mode_select_menu.append(btn)
        # 第二頁具體時間控制選項
        for btn in self.online_selection_buttons:
            self.online_mode_select_menu.append(btn)
        # 第二頁功能按鈕
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
        self.bot_combobox.append(self.combobox_coach)
        self.bot_combobox.append(self.combobox_adaptive)
        self.bot_combobox.append(self.combobox_beginner)
        self.bot_combobox.append(self.combobox_intermediate)
        self.bot_combobox.append(self.combobox_advanced)
        self.bot_combobox.append(self.combobox_master)
        self.bot_combobox.append(self.combobox_athletes)
        self.bot_combobox.append(self.combobox_musicians)
        self.bot_combobox.append(self.combobox_creators)
        self.bot_combobox.append(self.combobox_top_players)
        self.bot_combobox.append(self.combobox_personalities)
        self.bot_combobox.append(self.combobox_engine)

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

        self.bot_category_select_menu.append(self.returnToHomePageButton)        

        for item in self.bot_combobox:
            self.setting_layout.addWidget(item)
            item.hide()

        self.setting_layout.addWidget(self.play_button)
        self.play_button.hide()
        self.setting_layout.addWidget(self.back_to_category_button)
        self.back_to_category_button.hide()

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

        # 先加入 Setting 按鈕，再加入 Return Home Page 按鈕（會依各 menu 狀態顯示/隱藏）
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
        """
        重新套用目前語言的 UI 文字（切換語言時呼叫）。
        """
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

        self.playWithOtherButton.setText(t("ui.play.other.button"))
        self.playWithOtherButton.setAccessibleName(t("ui.play.other.name"))
        self.playWithOtherButton.setAccessibleDescription(t("ui.play.other.desc"))

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
        self.undo_button.setText(t("ui.undo.button"))
        self.resign.setText(t("ui.resign.button"))

        self.check_position.setPlaceholderText(t("ui.check_position.placeholder"))
        self.check_position.setAccessibleName(t("ui.check_position.name"))
        self.check_position.setAccessibleDescription(t("ui.check_position.desc"))

        self.commandPanel.setPlaceholderText(t("ui.command_panel.placeholder"))
        self.commandPanel.setAccessibleName(t("ui.command_panel.name"))
        self.commandPanel.setAccessibleDescription(t("ui.command_panel.desc"))

        self.selectPanel.setPlaceholderText(t("ui.select_panel.placeholder"))
