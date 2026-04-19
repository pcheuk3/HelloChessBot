import sys
import os
import re
import chess
import requests
from pathlib import Path
from dotenv import load_dotenv
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
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from PyQt6.QtCore import QUrl, Qt, QTimer, QThread, pyqtSignal, QSettings, QPoint
from PyQt6.QtGui import QFont, QShortcut, QKeySequence, QIcon, QGuiApplication


import Components.js_function as js_function    ## header file
from Components.piece_move_component import widgetDragDrop, widgetClick
from Components.chess_validation_component import ChessBoard
from Components.speak_component import TTSThread
from ui.chatbot_window import ChatbotWindow
from ui.left_widget import LeftWidget
from ui.right_widget import RightWidget
from ui.setting_window import SettingMenu
from Utils.i18n import t, set_language

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

def _get_app_base_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


BASE_DIR = _get_app_base_dir()
load_dotenv(BASE_DIR / ".env")
STT_SERVER_URL = os.getenv("STT_SERVER_URL", "https://hellochessbot.uk/stt")
APP_API_KEY = os.getenv("APP_API_KEY", "hddkqg3kiuddglwasbiajoijks")

import pyaudio
import wave

import time

PIECE_TYPE_CONVERSION = {
    "q": "queen",
    "n": "knight",
    "r": "rook",
    "b": "bishop",
    "p": "pawn",
    "k": "king",
    "none": "empty",
}

CHESSBOARD_LOCATION_CONVERSION = {
    "a": "1",
    "b": "2",
    "c": "3",
    "d": "4",
    "e": "5",
    "f": "6",
    "g": "7",
    "h": "8",
}

PIECES_SHORTFORM_CONVERTER = {
    "Q": "white queen",
    "N": "white knight",
    "R": "white rook",
    "B": "white bishop",
    "P": "white pawn",
    "K": "white king",

    "q": "black queen",
    "n": "black knight",
    "r": "black rook",
    "b": "black bishop",
    "p": "black pawn",
    "k": "black king",
}

# button setting for check box, button, and combo box: allow arrow key to select option
class CheckBox(QCheckBox):
    """
    CheckBox class that allowd check by enter
    """
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.nextCheckState()
        super(CheckBox, self).keyPressEvent(event)

class CustomButton(QPushButton):
    def keyPressEvent(self, event):
        # Only ignore arrow keys for this button
        if event.key() in [Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right]:
            event.ignore()
        else:
            super().keyPressEvent(event)

class CustomComboBox(QComboBox):
    """support arrow key to select option"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  
    
    def keyPressEvent(self, event):
        # when arrow key is pressed and ComboBox has focus, open the dropdown menu and select the option
        if event.key() == Qt.Key.Key_Up:
            if not self.view().isVisible():
                # if the dropdown menu is not opened, open it
                self.showPopup()
            # move to the previous option
            current_index = self.currentIndex()
            if current_index > 0:
                self.setCurrentIndex(current_index - 1)
            else:
                self.setCurrentIndex(self.count() - 1)
            # trigger the highlighted signal to read the current option
            self.highlighted.emit(self.currentIndex())
            event.accept()
        elif event.key() == Qt.Key.Key_Down:
            if not self.view().isVisible():
                # if the dropdown menu is not opened, open it
                self.showPopup()
            # move to the next option
            current_index = self.currentIndex()
            if current_index < self.count() - 1:
                self.setCurrentIndex(current_index + 1)
            else:
                self.setCurrentIndex(0)
            # trigger the highlighted signal to read the current option
            self.highlighted.emit(self.currentIndex())
            event.accept()
        elif event.key() == Qt.Key.Key_Enter or event.key() == Qt.Key.Key_Return:
            # Enter key confirm the selection
            if self.view().isVisible():
                self.hidePopup()
                self.currentIndexChanged.emit(self.currentIndex())
            else:
                super().keyPressEvent(event)
        elif event.key() == Qt.Key.Key_Escape:
            # Escape key close the dropdown menu but not change the selection
            if self.view().isVisible():
                self.hidePopup()
            else:
                event.ignore()
        else:
            # other keys use the default behavior
            super().keyPressEvent(event)
    
class confirmDialog(QDialog):
    """confirm popup dialog that show and speak the message"""
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("dialog.confirm.title"))
        QBtn = (
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        def dialog_helper_menu():
            speak(t("speak.common.confirm_or_cancel"))

        self.layout = QVBoxLayout()
        message = t("dialog.confirm.prefix", message=message)
        self.layout.addWidget(QLabel(message))
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

        shortcut_O = QShortcut(QKeySequence("Ctrl+O"), self)
        shortcut_O.activated.connect(dialog_helper_menu)
        shortcut_R = QShortcut(QKeySequence("Ctrl+R"), self)
        shortcut_R.activated.connect(partial(speak, message))
        speak(message)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Backspace or event.key() == Qt.Key.Key_Delete:
            print("cancel clicked")
            speak(t("speak.common.cancel"))
            self.reject()

class MainWindow(QMainWindow):
    """
    Merge left and right widget, and act as middle man for communication\n
    Control the application status, implement functionality to left and right widget.\n
    Handle all logic operation
    """
    keyPressed_Signal = pyqtSignal(int)

    def _get_resource_path(self, relative_path: str) -> str:
        return str(BASE_DIR / relative_path)

    def runJavaScriptSafe(self, jsCode, callback=None, close_overlays=True):

        try:
            page = self.leftWidget.chessWebView.page()
        except Exception:
            return

        def _run_target(_=None):
            try:
                if callback is None:
                    page.runJavaScript(jsCode)
                else:
                    page.runJavaScript(jsCode, callback)
            except Exception:
                if callback is not None:
                    try:
                        callback(None)
                    except Exception:
                        pass

        if not close_overlays:
            _run_target()
            return

        try:
            page.runJavaScript(js_function.dismissOverlays, _run_target)
        except Exception:
            _run_target()

    # check whether user logined
    def checkLogined(self):
        def callback(x):
            self.userLoginName = x
            print(f"Login User: {self.userLoginName}")
            if(self.userLoginName is not None):
                self.rightWidget.loginButton.hide()# hide and remove the login button
                self.rightWidget.setting_layout.removeWidget(self.rightWidget.loginButton)
                self.rightWidget.setting_menu.remove(self.rightWidget.loginButton)
            
                self.rightWidget.setting_layout.insertWidget(0, self.rightWidget.logoutButton)# add the logout button to the beginning of the layout
                self.rightWidget.logoutButton.show()
                self.rightWidget.logoutButton.setVisible(True)
                self.rightWidget.update()  # force update the layout
            self.currentFocus = len(self.rightWidget.setting_menu) - 1
            if self.rightWidget.loginButton.isVisible():
                self.rightWidget.loginButton.setFocus()
            elif self.rightWidget.logoutButton.isVisible():
                self.rightWidget.logoutButton.setFocus()

        jsCode = """
            function checkLogin() {{
                return document.querySelector(".home-user-info")?.outerText
            }}
            checkLogin();
            """
        self.runJavaScriptSafe(jsCode, callback)
##JS to click on web view button
    def clickWebButton(
        self, displayTextList, index, finalCallback, retry
    ):  ##avoid double load finish
        if index >= len(displayTextList):
            print("click finished")
            finalCallback()
            return True

        item = displayTextList[index]
        selector = ""
        expected_text = ""
        require_text_match = False

        if isinstance(item, (tuple, list)):
            if len(item) > 0:
                selector = item[0]
            if len(item) > 1 and item[1] is not None:
                expected_text = str(item[1])
            if len(item) > 2:
                require_text_match = bool(item[2])
        else:
            selector = str(item)

        if not selector:
            if retry < 10:
                QTimer.singleShot(
                    120,
                    lambda: self.clickWebButton(
                        displayTextList, index, finalCallback, retry + 1
                    ),
                )
                return False
            return False

        jsCode = f"""
            (function() {{
                const target = document.querySelector({repr(selector)});
                if (!target) {{
                    return "not_found";
                }}

                const expected = {repr(expected_text)}.trim().toLowerCase();
                const actual = (target.textContent || "").trim().toLowerCase();

                if ({'true' if require_text_match else 'false'} && expected && !actual.includes(expected)) {{
                    return "text_mismatch:" + actual;
                }}

                try {{
                    target.click();
                    return "clicked";
                }} catch (e) {{
                    return "click_error";
                }}
            }})();
        """

        def _on_click(result):
            result_text = str(result)
            if result_text == "clicked":
                QTimer.singleShot(
                    180,
                    lambda: self.clickWebButton(displayTextList, index + 1, finalCallback, 0),
                )
                return

            if retry < 18:
                QTimer.singleShot(
                    180,
                    lambda: self.clickWebButton(
                        displayTextList, index, finalCallback, retry + 1
                    ),
                )
                return

            print(f"clickWebButton failed at index {index}, selector={selector}, result={result_text}")

        self.runJavaScriptSafe(jsCode, _on_click, close_overlays=False)
        return False

    def _show_audio_reminder_on_startup(self):
        title = t("startup.audio_reminder.title")
        message = t("startup.audio_reminder.message")
        reminder_text = t("startup.audio_reminder.confirm", message=message)
        try:
            speak(reminder_text, True)
        except Exception:
            pass

        try:
            QMessageBox.information(self, title, reminder_text)
        except Exception:
            return

        self._audio_reminder_confirmed = True
        if self._welcome_pending:
            self._welcome_pending = False
            self._speak_welcome_message()

    def _speak_welcome_message(self):
        try:
            speak(
                t(Speak_template.welcome_sentense.value)
                + t(Speak_template.game_intro_sentense.value),
                True,
            )
        except Exception:
            pass

    def _load_time_control_from_txt(self):

        self.time_control_by_category = {}
        self.time_control_by_name = {}


        try:
            txt_path = str(BASE_DIR / "Components" / "time_control.txt")
        except Exception as e:
            print(f"resolve time_control.txt path failed: {e}")
            return

        if not os.path.exists(txt_path):
            print(f"time_control.txt not found at {txt_path}")
            return


        line_pattern = re.compile(r"^(\S+)\s+(.+?)\s{2,}(.+)$")
        fallback_pattern = re.compile(r"^(\S+)\s+(.+?)\s+(document\.querySelector\(.*\))$")

        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            print(f"read time_control.txt failed: {e}")
            return

        for raw in lines[1:]:
            line = raw.strip()
            if not line:
                continue
            m = line_pattern.match(line)
            if not m:
                m = fallback_pattern.match(line)
            if not m:
                continue
            category, name, js_expr = m.groups()
            self.time_control_by_category.setdefault(category, []).append(
                {"name": name, "js": js_expr}
            )

            self.time_control_by_name[name] = {"category": category, "js": js_expr}


    # User Login
    def loginHandler(self):
        def checkLogin(success):
            if(success):
                self.userLoginName = username
                # remember the current successful login account name, for automatic login next time
                try:
                    if hasattr(self, "settings"):
                        self.settings.setValue("last_username", self.userLoginName)
                except Exception:
                    pass
                # hide and remove the login button
                self.rightWidget.loginButton.hide()
                self.rightWidget.setting_layout.removeWidget(self.rightWidget.loginButton)
                self.rightWidget.setting_menu.remove(self.rightWidget.loginButton)
                # show the logout button after successful login
                # ensure the logout button is in the layout (if not, add it to the original login button position)
                logout_in_layout = False
                for i in range(self.rightWidget.setting_layout.count()):
                    widget = self.rightWidget.setting_layout.itemAt(i).widget()
                    if widget == self.rightWidget.logoutButton:
                        logout_in_layout = True
                        break
                
                if not logout_in_layout:
                    # if the logout button is not in the layout, add it to the beginning (the original login button position)
                    self.rightWidget.setting_layout.insertWidget(0, self.rightWidget.logoutButton)
                
                # show the logout button
                self.rightWidget.logoutButton.show()
                self.rightWidget.logoutButton.setVisible(True)
                self.rightWidget.update()  # force update the layout
                self.change_main_flow_status(Bot_flow_status.setting_status)
                print(f"login success! Username: {self.userLoginName}")
                speak(t("speak.login.success", username=self.userLoginName))
            else:
                print("The username or password is incorrect. Please try again")
                speak(t("speak.login.failed"))

        username = self.rightWidget.loginAccount_Input.text()
        password = self.rightWidget.loginPassword_Input.text()
        print(f"username: {username}")
        print(f"password: {password}")
        self.rightWidget.loginAccount_Input.clear()
        self.rightWidget.loginPassword_Input.clear()
        if(username == "" or password == ""):
            print("Invalid Input")
            speak(t("speak.login.invalid_input"))
            return
        self.runJavaScriptSafe(js_function.userLogin + f"userLogin('{username}', '{password}')")
        speak(t("speak.login.trying"))
        QTimer.singleShot(3000, lambda: self.runJavaScriptSafe(js_function.loginSuccess, checkLogin))

    # User Logout
    def logout(self):
        print("Logging out...")
        speak(t("speak.logout.logging_out"))
        
        profile = self.leftWidget.chessWebView.page().profile()
        # clear all cookies (this will clear the login status)
        profile.cookieStore().deleteAllCookies()
        # clear local storage (LocalStorage / IndexedDB etc.)
        profile.clearHttpCache()
        # clear the visited links
        profile.clearAllVisitedLinks()

        def performLogoutUI():
            """update the UI after logout"""
            self.rightWidget.logoutButton.hide()

            self.rightWidget.loginButton.show()
            
            # if the login button is not in the menu, add it to the menu
            if self.rightWidget.loginButton not in self.rightWidget.setting_menu:
                # find the logout button in the menu and insert the login button before it
                try:
                    logout_index = self.rightWidget.setting_menu.index(self.rightWidget.logoutButton)
                    self.rightWidget.setting_menu.insert(logout_index, self.rightWidget.loginButton)
                except ValueError:
                    # if the logout button is not found, add it to the beginning
                    self.rightWidget.setting_menu.insert(0, self.rightWidget.loginButton)
            

            logout_in_layout = False
            login_in_layout = False
            logout_index_in_layout = -1
            
            for i in range(self.rightWidget.setting_layout.count()):
                widget = self.rightWidget.setting_layout.itemAt(i).widget()
                if widget == self.rightWidget.logoutButton:
                    logout_in_layout = True
                    logout_index_in_layout = i
                if widget == self.rightWidget.loginButton:
                    login_in_layout = True
            
            if not login_in_layout and logout_in_layout:
                # insert the login button before the logout button
                self.rightWidget.setting_layout.insertWidget(logout_index_in_layout, self.rightWidget.loginButton)
            elif not login_in_layout:
                # if the logout button is not found, add it to the beginning
                self.rightWidget.setting_layout.insertWidget(0, self.rightWidget.loginButton)
            
            # clear the login user name
            self.userLoginName = ""
            
            # reload the chess.com homepage (now it should be the unlogged state)
            self.leftWidget.chessWebView.load(QUrl("https://www.chess.com"))
            
            self.change_main_flow_status(Bot_flow_status.setting_status)
            
            print("Logout successful")
            speak(t("speak.logout.success"))
            
            # #region agent log
            try:
                with open(log_path, 'a', encoding='utf-8') as log_file:
                    log_entry = {
                        "timestamp": int(time.time() * 1000),
                        "location": "MainWindow.logout",
                        "message": "Logout completed",
                        "data": {"userLoginName": self.userLoginName}
                    }
                    log_file.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            except Exception as e:
                pass
            # #endregion agent log
        
        QTimer.singleShot(500, performLogoutUI)

    def _hide_all_right_widgets(self):
        try:
            for i in range(self.rightWidget.setting_layout.count()):
                w = self.rightWidget.setting_layout.itemAt(i).widget()
                if w:
                    w.hide()
        except Exception:
            pass
        try:
            for scroll in self.rightWidget.bot_category_lists.values():
                scroll.hide()
        except Exception:
            pass

    ##change the application flow status and re-init / clean the variable
    def change_main_flow_status(self, status):
        print("change status", status)

        if status == Bot_flow_status.select_status and self.main_flow_status == Bot_flow_status.select_status:
            return

        self._hide_all_right_widgets()
        match status:
            case Bot_flow_status.login_status:
                speak(t("speak.flow.activate_login_input"))
                self.leftWidget.chessWebView.load(QUrl("https://www.chess.com/login"))
                self.main_flow_status = Bot_flow_status.login_status
                self.currentFocus = len(self.rightWidget.login_menu) - 1
                for item in self.rightWidget.login_menu:
                    item.show()
                self.rightWidget.loginAccount_Input.setFocus()

            case Bot_flow_status.setting_status:
                self.getOpponentMoveTimer.stop()
                self.check_game_end_timer.stop()
                self.getScoreTimer.stop()
                self.main_flow_status = Bot_flow_status.setting_status
                self.game_play_mode = None
                self.online_game_started = False
                self.input_mode = Input_mode.command_mode
                self.alphabet = ["A", "B", "C", "D", "E", "F", "G", "H"]
                self.number = ["1", "2", "3", "4", "5", "6", "7", "8"]
                self.moveList_line = 1
                self.moveList_element = 0
                self.moveListString = ""
                self.chessBoard = None
                self.change_game_mode(None)
                self.rightWidget.colorBox.setText(t("ui.assigned_color"))
                self.userColor = None
                self.opponentColor = None
                self.category_combobox = None
                self.selected_bot_name = None
                self.selected_bot_category = None
                self.selected_bot_level = None
                self.bot_retry = False
                self._last_opponent_row_sig = ""
                self.rightWidget.right_layout = self.rightWidget.setting_layout
                self.rightWidget.opponentBox.setText(t("ui.opponent_last_move"))
                try:
                    for i in range(8):
                        for j in range(8):
                            if(isinstance(self.leftWidget.grids[i][j], QLabel)):
                                self.leftWidget.grids[i][j].deleteLater()
                except:
                    print("No grids need to delete")
                for item in self.rightWidget.setting_menu:
                    item.show()
                self.currentFocus = -1
                return
                
            case Bot_flow_status.select_status:
                self.main_flow_status = Bot_flow_status.select_status
                self.game_flow_status = Game_flow_status.not_start
                match self.game_play_mode:
                    case Game_play_mode.computer_mode:
                        self.currentFocus = -1
                        for item in self.rightWidget.bot_category_select_menu:
                            item.show()
                        for scroll in self.rightWidget.bot_category_lists.values():
                            scroll.hide()
                        self.runJavaScriptSafe(js_function.open_bot_menu)
                        speak(t("speak.flow.select_bot_category"))
                    case Game_play_mode.online_mode:
             
                        self.open_online_category_page()
                return

            case Bot_flow_status.board_init_status:
                self.main_flow_status = Bot_flow_status.board_init_status

                self.leftWidget.chessWebView.loadFinished.connect(
                    partial(print, "connect")
                )
                self.leftWidget.chessWebView.loadFinished.disconnect()
                self.getOpponentMoveTimer.stop()
                self.check_game_end_timer.stop()
                self.getScoreTimer.stop()
                self.input_mode = Input_mode.command_mode
                for item in self.rightWidget.play_menu:
                    item.show()
                self.chessBoard = None
                self.userColor = None
                self.opponentColor = None
                # self.leftWidget.grids = dict()
                return
            
            case Bot_flow_status.game_play_status:
                self.check_game_end_timer.start(2000)
                self.rightWidget.commandPanel.setFocus()
                self.currentFocus = len(self.rightWidget.play_menu) - 1
                self.main_flow_status = Bot_flow_status.game_play_status
 
                for item in self.rightWidget.play_menu:
                    item.show()
     
                try:
                    if self.game_play_mode == Game_play_mode.online_mode:
                        self.rightWidget.check_time.show()
                    else:
                        self.rightWidget.check_time.hide()
                except Exception:
                    pass
                return
            
            case Bot_flow_status.game_end_status:
                self.moveList_line = 1
                self.moveList_element = 0
                self.arrow_mode_switch(False)
                self.input_mode = Input_mode.command_mode
                self.getOpponentMoveTimer.stop()
                self.check_game_end_timer.stop()
                self.getScoreTimer.stop()
                self.rightWidget.whitePieces.setText(t("ui.white_pieces"))
                self.rightWidget.blackPieces.setText(t("ui.black_pieces"))
                self.input_mode = Input_mode.command_mode
                self.chessBoard = None
                for item in self.rightWidget.game_end_menu:
                    item.show()
                self.currentFocus = len(self.rightWidget.game_end_menu) - 1
                self.main_flow_status = Bot_flow_status.game_end_status

            case Bot_flow_status.puzzle_end_status:
                self.arrow_mode_switch(False)
                self.input_mode = Input_mode.command_mode
                self.main_flow_status = Bot_flow_status.puzzle_end_status
                for item in self.rightWidget.puzzle_end_menu:
                    item.show()
                self.currentFocus = len(self.rightWidget.puzzle_end_menu) - 1

    ##change the application game mode
    def change_game_mode(self, mode):
        match mode:
            case None:
                self.game_play_mode = None
            case Game_play_mode.analysis_mode:
                self.currentFocus = len(self.rightWidget.analysis_menu) - 1
                self.game_play_mode = Game_play_mode.analysis_mode
                self._hide_all_right_widgets()
                for item in self.rightWidget.analysis_menu:
                    item.show()

    ##initialize a vs computer game for user
    def playWithComputerHandler(self):
        if self.main_flow_status == Bot_flow_status.board_init_status:
            speak(
                t(
                    "speak.game.still_initializing",
                    sentence=t(Speak_template.initialize_game_sentense.value),
                ),
                True,
            )
            return
        if (
            self.main_flow_status == Bot_flow_status.game_play_status
            and not self.game_flow_status == Game_flow_status.game_end
        ):
            speak(t("speak.game.resign_before_new"), True)
            return
        print("computer mode selected")
        self.game_play_mode = Game_play_mode.computer_mode
        speak(
            t(
                "speak.game.computer_mode_selected",
                sentence=t(Speak_template.initialize_game_sentense.value),
            ),
            True,
        )

        self.change_main_flow_status(Bot_flow_status.select_status)
        self.leftWidget.chessWebView.loadFinished.connect(lambda: QTimer.singleShot(4000, self.checkExistGame))

        self.leftWidget.chessWebView.load(
            QUrl("https://www.chess.com/play/computer")
        )

    ##initialize a vs online player game for user
    def playWithOtherButtonHandler(self):  ###url
        if self.main_flow_status == Bot_flow_status.board_init_status:
            speak(
                t(
                    "speak.game.still_initializing",
                    sentence=t(Speak_template.initialize_game_sentense.value),
                ),
                True,
            )
            return
        if (
            self.main_flow_status == Bot_flow_status.game_play_status
            and not self.game_flow_status == Game_flow_status.game_end
        ):
            speak(t("speak.game.resign_before_new"), True)
            return
        print("online mode selected")
        speak(
            t(
                "speak.game.online_mode_selected",
                sentence=t(Speak_template.initialize_game_sentense.value),
            ),
            True,
        )
        self.game_play_mode = Game_play_mode.online_mode

        self.change_main_flow_status(Bot_flow_status.select_status)
        self.leftWidget.chessWebView.loadFinished.connect(lambda: QTimer.singleShot(3000, self.checkExistGame))
        self.leftWidget.chessWebView.load(QUrl("https://www.chess.com/play/online"))

    def selectPanelHandler(self):
        input = self.rightWidget.selectPanel.text().lower()
        if(self.game_play_mode == Game_play_mode.computer_mode):
            print("no idea")
        elif(self.game_play_mode == Game_play_mode.online_mode):
            return
    
    # handle select timecontrol
    def online_select_timeControl(self, timeControl, skip=False):
        def board():
            self.getColor()
            self.initBoard()
            self.getBoard()
            self.online_game_started = True

        def poll_online_game_ready(_=None, retry=0):
            if self.main_flow_status == Bot_flow_status.setting_status or self.game_play_mode != Game_play_mode.online_mode:
                return

            def ready_callback(ready):
                if self.main_flow_status == Bot_flow_status.setting_status or self.game_play_mode != Game_play_mode.online_mode:
                    return

                if ready:
                    print("online game is ready")
                    QTimer.singleShot(1000, board)
                elif retry < 24:
                    if self.main_flow_status == Bot_flow_status.game_play_status and self.chessBoard is not None:
                        self.online_game_started = True
                        return
                    QTimer.singleShot(1000, lambda: poll_online_game_ready(None, retry + 1))
                else:
                    print("online game not ready in time")

                    def _status_callback(status):
                        status_text = (str(status) if status is not None else "").strip()
                        if status_text in ("time_not_selected", "start_not_ready"):
                            remind = t("speak.game.online_page_not_ready")
                            speak(remind)
                            self._append_chatbot_system_message(remind)
                        else:
                            speak(t("speak.game.match_not_started"))

                        self.online_game_started = False
                        self.change_main_flow_status(Bot_flow_status.select_status)

                    self.runJavaScriptSafe(
                        "(function(){ return window.__neoOnlineSetupStatus || ''; })();",
                        _status_callback,
                        close_overlays=False,
                    )

            self.runJavaScriptSafe(js_function.onlineGameReady, ready_callback)

        print(f"timeControl = {timeControl}")
        self.timeControl = timeControl
        self.online_game_started = False

        if(skip):
            self.leftWidget.chessWebView.loadFinished.disconnect()

        for item in self.rightWidget.online_mode_select_menu:
            item.hide()

        for item in self.rightWidget.play_menu:
            item.show()
        selected = self.time_control_by_name.get(timeControl, {})
        selected_js_expr = selected.get("js", "")
        js_selector_arg = repr(selected_js_expr)

        start_selector = "#board-layout-sidebar > div.sidebar-content > div.new-game-component > div.new-game-primary > button"
        selected_selector = None
        if selected_js_expr:
            m = re.search(r'document\.querySelector\("([^"]+)"\)', selected_js_expr)
            if m:
                selected_selector = m.group(1)

        if selected_selector:

            self.clickWebButton(
                [
                    (selected_selector, ""),
                    (start_selector, ""),
                ],
                0,
                lambda: poll_online_game_ready(None, 0),
                0,
            )
            return

        if self.userLoginName != None:
            print("login name", self.userLoginName)
            self.runJavaScriptSafe(
                js_function.clickTimeControlButton + f"clickTimeControlButton('{timeControl}', true, {js_selector_arg}, '{start_selector}')",
                poll_online_game_ready,
            )
        else:
            print("No login")
            no_login_text = "No login detected. Continuing as guest mode."
            speak(no_login_text)
            self._append_chatbot_system_message(no_login_text)
            self.runJavaScriptSafe(
                js_function.clickTimeControlButton + f"clickTimeControlButton('{timeControl}', false, {js_selector_arg}, '{start_selector}')",
                poll_online_game_ready,
            )

    #handle select bot
    def select_bot(self):
        def callback1(x):
            print("select bot")
            if(self.bot_retry):
                QTimer.singleShot(1000, lambda: self.runJavaScriptSafe(js_function.select_bot + f"select_bot('{self.selected_bot_name}');"))
                QTimer.singleShot(2000, lambda: self.runJavaScriptSafe(js_function.check_bot_locked, callback2, close_overlays=False))
                return
            QTimer.singleShot(1000, lambda: self.runJavaScriptSafe(js_function.check_bot_locked, callback2, close_overlays=False))

        def callback2(locked_info):
            print(f"locked = {locked_info}")

            locked = False
            lock_type = "none"
            lock_message = ""
            if isinstance(locked_info, dict):
                locked = bool(locked_info.get("locked"))
                lock_type = str(locked_info.get("type", "none"))
                lock_message = str(locked_info.get("message", ""))
            else:
                locked = bool(locked_info)

            if(locked):
                # self.leftWidget.chessWebView.load(
                #     QUrl("https://www.chess.com/play/computer")
                # )
                if lock_type == "login":
                    remind = "detected login popup: this bot requires login to use, otherwise the game cannot be started."
                elif lock_type == "vip":
                    remind = "detected VIP/membership popup: this bot may require paid membership to use, otherwise the game cannot be started."
                else:
                    remind = "detected limit popup: this bot cannot be started, please select other bot."

                if lock_message:
                    remind = remind + f" popup content: {lock_message}"

                speak(remind)
                self._append_chatbot_system_message(remind)
                self.bot_retry = True
            else:
                if self.selected_bot_category:
                    selected_list = self.rightWidget.bot_category_lists.get(self.selected_bot_category)
                    if selected_list:
                        selected_list.hide()
                self.rightWidget.play_button.hide()
                self.rightWidget.back_to_category_button.hide()
                self.rightWidget.bot_list_hint_label.hide()
                for item in self.rightWidget.play_menu:
                    item.show()
                board()
                speak(t("speak.game.bot_started"))

        def board():
            self.getColor()
            self.initBoard()
            self.getBoard()

        if self.selected_bot_name is None:
            return
        print(f"Bot: {self.selected_bot_name}")
        if self.selected_bot_level is not None:
            level = self.selected_bot_level
            print(level)
            self.runJavaScriptSafe(js_function.select_engine_level + f"select_engine_level('{level}');", callback1)
            return

        self.runJavaScriptSafe(js_function.select_bot + f"select_bot('{self.selected_bot_name}');", callback1)

    #handle select bot category
    def bot_select_category(self, category):
        for item in self.rightWidget.bot_category_select_menu:
            item.hide()
        self.selected_bot_category = category
        self.selected_bot_name = None
        self.selected_bot_level = None
        # reset selection state for this category
        try:
            if hasattr(self.rightWidget, "bot_buttons_group"):
                self.rightWidget.bot_buttons_group.setExclusive(False)
                for btn in self.rightWidget.bot_category_buttons.get(category, []):
                    btn.setChecked(False)
                self.rightWidget.bot_buttons_group.setExclusive(True)
        except Exception:
            pass
        selected_list = self.rightWidget.bot_category_lists.get(category)
        if selected_list:
            selected_list.show()
        self.rightWidget.play_button.hide()
        self.rightWidget.back_to_category_button.show()
        self.rightWidget.bot_list_hint_label.show()

        self.currentFocus = -1
        try:
            if selected_list and self.rightWidget.bot_category_buttons.get(category):
                self.rightWidget.bot_category_buttons[category][0].setFocus()
        except Exception:
            pass
        speak(t("speak.game.select_bot_then_start"))

    #function for return to category selection
    def back_to_category(self):
        print("Return to Category")
        if self.selected_bot_category:
            selected_list = self.rightWidget.bot_category_lists.get(self.selected_bot_category)
            if selected_list:
                selected_list.hide()
        self.rightWidget.play_button.hide()
        self.rightWidget.back_to_category_button.hide()
        for item in self.rightWidget.bot_category_select_menu:
            item.show()
        self.rightWidget.bot_list_hint_label.hide()
        self.selected_bot_name = None
        self.selected_bot_category = None
        self.selected_bot_level = None

        self.currentFocus = -1
        try:
            if self.rightWidget.bot_category_select_menu:
                self.rightWidget.bot_category_select_menu[0].setFocus()
        except Exception:
            pass

    #function to speak out selected bot
    def bot_information(self, index, select=False):
        print(index)
        if(select):
            print(index)
            if self.selected_bot_name:
                speak(t("speak.game.bot_selected", name=self.selected_bot_name))
            return
        if self.selected_bot_name:
            speak(self.selected_bot_name)

    def select_bot_from_button(self, button):
        if button is None:
            return
        self.selected_bot_name = str(button.property("bot_name") or "")
        self.selected_bot_category = str(button.property("bot_category") or "")
        level_value = button.property("bot_level")
        self.selected_bot_level = int(level_value) if level_value is not None else None
        speak(t("speak.game.bot_selected", name=self.selected_bot_name))

    #function to check whether unfinished game exist
    def checkExistGame(self):
        if self._checking_exist_game:
            return

        if self.main_flow_status in (Bot_flow_status.game_play_status, Bot_flow_status.board_init_status):
            return
        self._checking_exist_game = True
        self.online_game_started = False

        def callback(moveList):
            print(f"movemovmeomvomeovmo = {moveList}")

            self._checking_exist_game = False
            if(moveList):
                self.change_main_flow_status(Bot_flow_status.board_init_status)
                self.getColor(exist_game=t("speak.game.existing_game_found"))
                self.initBoard()
                print("reconstructing the board")
                self.getBoard()

                for move in moveList:
                    print(self.moveList_element)
                    if(self.moveList_element % 10 == 0 and self.moveList_element != 0):
                        self.moveListString += "\n"
                    if (self.moveList_element % 2 == 0):
                        self.moveListString += str(self.moveList_line) + ". " + self.chessBoard.board_object.parse_san(move).uci() + ", "
                    else:
                        self.moveListString += self.chessBoard.board_object.parse_san(move).uci() + ", "
                        self.moveList_line += 1
                    self.moveList_element += 1
                    if(self.moveList_element == len(moveList)):
                        self.rightWidget.opponentBox.setText(f"opponent last move: {self.chessBoard.board_object.parse_san(move).uci()}")
                    self.chessBoard.board_object.push_san(move)
                self.rightWidget.moveList.setText(t("ui.move_list") + "\n" + self.moveListString)
        
                print(self.chessBoard.board_object)
                self.previous_game_exist = True
                turn = "WHITE" if(self.moveList_element %2==0) else "BLACK"
                print(f"current turn: {turn}")
                self.game_flow_status = Game_flow_status.user_turn if(turn==self.userColor) else Game_flow_status.opponent_turn
                print("Existing Game Founded")

                self.change_main_flow_status(Bot_flow_status.game_play_status)
                return

            else:
                print("no existing board")

                if self.main_flow_status != Bot_flow_status.game_play_status:
                    self.change_main_flow_status(Bot_flow_status.select_status)


        try:
            self.leftWidget.chessWebView.loadFinished.disconnect()
        except TypeError:

            pass
        self.runJavaScriptSafe(js_function.checkExistGame, callback)

    def getPiecesLocation(self, location):
        self.rightWidget.whitePieces.setText(f"{t('ui.white_pieces')}" + location[0])
        self.rightWidget.blackPieces.setText(f"{t('ui.black_pieces')}" + location[1])


## Puzzle Mode Start:

    def puzzleModeHandler(self):
        if(self.game_flow_status == Bot_flow_status.game_play_status):
            return
        speak(t(Speak_template.initialize_game_sentense.value), True)
        self.main_flow_status = self.change_main_flow_status(Bot_flow_status.board_init_status)
        self.leftWidget.chessWebView.load(QUrl("https://www.chess.com/puzzles/rated"))
        self.leftWidget.chessWebView.loadFinished.connect(lambda: QTimer.singleShot(4000, self.puzzle_mode_InitBoard))

    def puzzle_mode_InitBoard(self):
        try:
            self.leftWidget.chessWebView.loadFinished.disconnect()
        except:
            print("no load finish connected")
        self.getOpponentMoveTimer.stop()
        self.rightWidget.resign.hide()
        self.rightWidget.check_time.hide()
        self.rightWidget.moveList.hide()

        try:
            self.rightWidget.undo_button.hide()
        except Exception:
            pass
        self.count = 0
        self.puzzle_mode_GetTitle()

    def puzzle_mode_GetTitle(self):
        def callback(title):
            if(self.userColor == None):
                match title:
                    case "White":
                        self.row, self.col = 0, 0
                        self.userColor = title.upper()
                        self.opponentColor = "BLACK"
                        self.currentPos = 'a1'
                        print(f"User: {self.userColor}, Oppoenent: {self.opponentColor}")
                    case "Black":
                        self.row, self.col = 7, 7
                        self.userColor = title.upper()
                        speak(t("speak.template.user_black_side_sentence"))
                        self.opponentColor = "WHITE"
                        self.currentPos = 'h8'
                        print(f"User: {self.userColor}, Oppoenent: {self.opponentColor}")
                
                try:
                    self.rightWidget.colorBox.setText(f"{t('ui.assigned_color')} {self.userColor}")
                    self.puzzle_mode_ConstructBoard()
                except:
                    speak(t("speak.puzzle.limit_reached"))
                    self.leftWidget.chessWebView.load(QUrl("https://www.chess.com"))
                    self.change_main_flow_status(Bot_flow_status.setting_status)
            else:
                match title:
                    case "Correct" | "Solved":
                        print("Correct")
                        speak(t("speak.puzzle.correct_next_action"))
                        self.game_flow_status = self.change_main_flow_status(Bot_flow_status.puzzle_end_status)
                    #button click next
                    case "Incorrect":
                        print("Incorrect, puzzle run ended. Please select next action.")
                        speak(t("speak.puzzle.incorrect_ended"))
                        self.change_main_flow_status(Bot_flow_status.puzzle_end_status)
                    case _:
                        # self.puzzle_getOppMove_sgn.emit()
                        self.puzzle_mode_GetMove()

        self.runJavaScriptSafe(js_function.puzzle_mode_GetTitle, callback)

    def puzzle_mode_ConstructBoard(self):
        def callback(board):
            self.FenNotation = ""
            self.boardDescription = []
            self.whiteLoc = []
            self.blackLoc = []
            for row in reversed(range(8)):
                count = 0
                for column in range(8):
                    if(board[row][column]!=0):
                        alphabet_column = list(CHESSBOARD_LOCATION_CONVERSION.keys())[list(CHESSBOARD_LOCATION_CONVERSION.values()).index(str(column+1))]  #find the alphabet form column
                        piece_loc = PIECES_SHORTFORM_CONVERTER[board[row][column]] + ": " + alphabet_column + str(row+1)
                        if(board[row][column] in ['Q', 'N', 'R', 'B', 'P', 'K']):
                            self.whiteLoc.append(piece_loc)
                        else:
                            self.blackLoc.append(piece_loc)
                        self.boardDescription.append(piece_loc)
                        if(count!=0):
                            self.FenNotation += str(count) + board[row][column]
                            count = 0
                        else:
                            self.FenNotation += board[row][column]
                    else:
                        count += 1
                        if(column==7):
                            self.FenNotation += str(count)
                    print(board[row][column], end=" ")
                if(row!=0):
                    self.FenNotation += "/"
                print()
            if(self.userColor=="WHITE"):
                self.FenNotation += " w "
                if(board[0][4]=="K"):
                    if(board[0][0]=="R"):
                        self.FenNotation += "K"
                    if(board[0][7]=="R"):
                        self.FenNotation += "Q"
                self.FenNotation += "kq"
            else:
                self.FenNotation += " b KQ"
                if(board[7][4]=="k"):
                    if(board[7][7]=="r"):
                        self.FenNotation += "k"
                    if(board[7][0]=="r"):
                        self.FenNotation += "q"
            print(self.FenNotation)
            print(self.boardDescription)
            print(self.whiteLoc)
            print(self.blackLoc)
            self.rightWidget.commandPanel.setFocus()
            self.currentFocus = len(self.rightWidget.play_menu) - 1
            self.main_flow_status = Bot_flow_status.game_play_status
            self.game_play_mode = Game_play_mode.puzzle_mode
            self.chessBoard = ChessBoard(self.FenNotation)
            self.game_flow_status = Game_flow_status.opponent_turn
            self.puzzle_mode_GetTitle()

        self.initBoard()
        self.runJavaScriptSafe(js_function.puzzle_mode_constructBoard, callback)

    def puzzle_mode_GetMove(self):
        def callback(uci_move):
            print(uci_move)
            # next/retry puzzle may need a short delay before highlight squares are available
            if (
                self.main_flow_status != Bot_flow_status.game_play_status
                or self.game_play_mode != Game_play_mode.puzzle_mode
                or self.game_flow_status != Game_flow_status.opponent_turn
            ):
                return

            if self.chessBoard is None:
                QTimer.singleShot(350, self.puzzle_mode_GetMove)
                return

            if not isinstance(uci_move, str):
                QTimer.singleShot(350, self.puzzle_mode_GetMove)
                return

            uci_move = uci_move.strip().upper()
            if len(uci_move) < 4:
                QTimer.singleShot(350, self.puzzle_mode_GetMove)
                return

            pos1 = uci_move[0] + uci_move[1]
            pos2 = uci_move[2] + uci_move[3]
            pos1_piece = self.chessBoard.check_grid(pos1)
            print(f'pos1_piece = {pos1_piece}')
            print(f"count = {self.count}")
            if(self.count == 0):
                if(pos1_piece == None):
                    dest = pos2
                    src = pos1
                else:
                    dest = pos1
                    src = pos2
            else:
                if(pos1_piece == None):
                    dest = pos1
                    src = pos2
                else:
                    dest = pos2
                    src = pos1
            if(self.game_flow_status == Game_flow_status.opponent_turn):
                print(f"Opponent Last Move: {src} to {dest}")
                speak(t("speak.game.opponent_last_move", src=src, dest=dest))
                if(self.count != 0):
                    self.chessBoard.moveWithValidate(src + dest)
                    print(self.chessBoard.board_object)
                self.count += 1
                self.rightWidget.opponentBox.setText(f"Opponent Last Move: {src} to {dest}")
                if(self.count == 1):
                    if self.userColor == "WHITE":
                        speak("You are playing as white\n" + self.rightWidget.whitePieces.text() + self.rightWidget.blackPieces.text() + self.rightWidget.opponentBox.text())
                    else:
                        speak("You are playing as black\n" + self.rightWidget.whitePieces.text() + self.rightWidget.blackPieces.text() + self.rightWidget.opponentBox.text())
                self.game_flow_status = Game_flow_status.user_turn
            else:
                print("no update move")
                return
            
            self.runJavaScriptSafe(js_function.getPiecesLocation, self.getPiecesLocation)

        if self.input_mode == Input_mode.arrow_mode:
            self.all_grids_switch(True)
        self.runJavaScriptSafe(js_function.puzzle_mode_GetOpponentMove, callback)

    def puzzle_movePiece(self, move):
        movePair = self.chessBoard.moveWithValidate(move)
        print(self.chessBoard.board_object)
        san_string = ""
        uci_string = ""
        human_string = ""
        if len(movePair) == 2:
            uci_string = movePair[0]
            san_string = movePair[1]
            human_string = self.move_to_human_form(
                self.userColor, uci_string, san_string
            )

            # movePair = movePair[0]

        if len(uci_string) == 5:

            target_col = int(CHESSBOARD_LOCATION_CONVERSION[uci_string[0].lower()]) - 1 
            target_row = int(uci_string[1]) - 1
            dest_col = int(CHESSBOARD_LOCATION_CONVERSION[uci_string[2].lower()]) - 1   #index
            dest_row = int(uci_string[3]) - 1
            dest = uci_string[2:4]
            print(f"dest_row: {dest_row}, dest_col: {dest_col}")
            promoteTo = uci_string[4].lower()
            promote_index = list(PIECE_TYPE_CONVERSION).index(promoteTo)

            print(f"promote_index: {promote_index}")

            # dlg = confirmMoveDialog("pawn", dest, promote=promoteTo)
            dlg = confirmDialog(human_string)
            if dlg.exec():
                self.all_grids_switch(False)
                targetWidget = self.leftWidget.grids[target_col][target_row]
                destWidget = self.leftWidget.grids[dest_col][dest_row]
                if widgetDragDrop(targetWidget, destWidget):
                    match self.userColor:
                        case "BLACK":
                            promoteRow = dest_row + promote_index
                        case "WHITE":
                            promoteRow =  dest_row - promote_index
                    print(f"dest_col: {dest_col}, promoteRow: {promoteRow}")
                    promoteWidget = self.leftWidget.grids[dest_col][promoteRow]
                    if widgetClick(promoteWidget):
                        self.rightWidget.commandPanel.clear()
                        self.game_flow_status = Game_flow_status.opponent_turn
                        QTimer.singleShot(500, self.focus_back)
            else:
                self.chessBoard.board_object.pop()
                self.rightWidget.commandPanel.clear()
                self.game_flow_status = Game_flow_status.user_turn
                try:
                    self._latest_web_fen = None
                    self._latest_web_fen_time = 0
                    self._refresh_fen_from_web(reason="cancel_move")
                except Exception:
                    pass
                print("Cancel!")

        elif len(uci_string) == 4:

            target_col = int(CHESSBOARD_LOCATION_CONVERSION[uci_string[0].lower()]) - 1
            target_row = int(uci_string[1]) - 1
            dest_col = int(CHESSBOARD_LOCATION_CONVERSION[uci_string[2].lower()]) - 1
            dest_row = int(uci_string[3]) - 1
            dest = uci_string[2:4]
            # dlg = confirmMoveDialog(target_type, dest)
            dlg = confirmDialog(human_string)
            if dlg.exec():
                self.all_grids_switch(False)
                # QTimer.singleShot(3000, partial(self.clickStart,input))
                # print(self.chessBoard.board_object)

                targetWidget = self.leftWidget.grids[target_col][target_row]
                destWidget = self.leftWidget.grids[dest_col][dest_row]
                self.rightWidget.commandPanel.clear()
                if widgetDragDrop(targetWidget, destWidget):
                    self.game_flow_status = Game_flow_status.opponent_turn
                    QTimer.singleShot(500, self.focus_back)
            else:
                self.chessBoard.board_object.pop()
                self.rightWidget.commandPanel.clear()
                self.game_flow_status = Game_flow_status.user_turn
                try:
                    self._latest_web_fen = None
                    self._latest_web_fen_time = 0
                    self._refresh_fen_from_web(reason="cancel_move")
                except Exception:
                    pass
                print("Cancel!")
        elif movePair == "Promotion":
            print("Promotion")
            speak(
                "Please indicate the promotion piece by typing the first letter"
            )
            self.rightWidget.commandPanel.setFocus()
        else:
            error_text = move + movePair
            speak(error_text)
            print(error_text)  ##error move speak
            self._append_chatbot_system_message(error_text)
            self.rightWidget.commandPanel.clear()
        
        QTimer.singleShot(1000, self.puzzle_mode_GetTitle)
        QTimer.singleShot(500, lambda: self.runJavaScriptSafe(js_function.getPiecesLocation, self.getPiecesLocation))

    def clickNextPuzzle(self):
        def callback(x):
            self.userColor = None
            self.change_main_flow_status(Bot_flow_status.board_init_status)
            QTimer.singleShot(2000, self.puzzle_mode_InitBoard)

        self.runJavaScriptSafe(js_function.clickNextPuzzle, callback)

    def retryPuzzle(self):
        def callback(x):
            self.userColor = None
            self.change_main_flow_status(Bot_flow_status.board_init_status)
            QTimer.singleShot(2000, self.puzzle_mode_InitBoard)

        self.runJavaScriptSafe(js_function.retryPuzzle, callback)

## Puzzle Mode End

    ##convert move to human readable form
    def move_to_human_form(self, attackerColor, uciString, sanString):
        counter_color = "WHITE" if attackerColor == "BLACK" else "BLACK"
        human_string = attackerColor
        uciString = str(uciString).lower()
        san_raw = str(sanString)
        san_lower = san_raw.lower()
        target_square = uciString[:2]
        dest_square = uciString[2:4]

        self.chessBoard.board_object.pop()

        en_passant = self.chessBoard.board_object.has_legal_en_passant()
        target_piece_type = self.chessBoard.check_grid(target_square).__str__().lower()

        dest_piece_type = self.chessBoard.check_grid(dest_square).__str__().lower()

        print(target_piece_type, dest_piece_type)
        # self.chessBoard.moveWithValidate(san_raw)
        if san_lower.count("x"):
            human_string = (
                human_string
                + " "
                + PIECE_TYPE_CONVERSION[target_piece_type]
                + " captures"
            )
            if en_passant and target_piece_type == "p" and dest_piece_type == None:
                human_string = (
                    human_string + " on " + dest_square.upper() + " en passant"
                )
            else:
                human_string = (
                    human_string
                    + " "
                    + counter_color
                    + " "
                    + PIECE_TYPE_CONVERSION[dest_piece_type]
                    + " on "
                    + dest_square.upper()
                )
        else:
            human_string = (
                human_string
                + " "
                + PIECE_TYPE_CONVERSION[target_piece_type]
                + " moves to "
                + dest_square
            )

        if "o-o-o" in san_lower:
            human_string = human_string + " queenside castling"
        elif "o-o" in san_lower:
            human_string = human_string + " kingside castling"
        elif "=" in san_raw:
            human_string = (
                human_string
                + " and promoted to "
                + PIECE_TYPE_CONVERSION[
                    san_raw[san_raw.index("=") + 1].__str__().lower()
                ]
            )

        if "+" in san_raw:
            human_string = human_string + " and check "


        restore_result = self.chessBoard.moveWithValidate(uciString)
        if not (isinstance(restore_result, tuple) and len(restore_result) == 2):

            self.chessBoard.moveWithValidate(san_raw)

        print(human_string)
        return human_string

    ##check the score when end game
    def check_score(self):
        def callBack(x):
            if (
                not self.game_flow_status == Game_flow_status.game_end
                or not self.game_play_mode == Game_play_mode.online_mode
            ):
                self.getScoreTimer.stop()
                return
            if not x == None and (x[0] or x[1]):
                speak_string = ""
                print("rating: ", x[0], "league: ", x[1])
                if not x[0] == None:
                    speak_string = speak_string + "rating " + x[0]
                if not x[1] == None:
                    speak_string = speak_string + "league " + x[1]
                self.getScoreTimer.stop()
                speak(speak_string)
            else:
                self.getScoreTimer.start(1000)

        jsCode = """
            function checkScore(){{
                rating = document.querySelectorAll(".rating-score-component")[1]
                league = document.querySelectorAll(".league-score-component")[0]

                if(!rating.textContent){{
                    rating = null 
                }}
                else{{
                    rating = rating.textContent?.trim()
                }}

                if(!league.textContent){{
                    league = null 
                }}
                else{{
                    league = rating.textContent?.trim()
                }}
                return [rating, league]
            }}

            checkScore();
        """
        return self.runJavaScriptSafe(jsCode, callBack)

    ##click resign button on web view
    def resign_handler(self):
        dlg = confirmDialog(t("dialog.confirm.resign_message"))
        if dlg.exec():
            def callBack():
     
                self.change_main_flow_status(Bot_flow_status.game_end_status)
                self.game_flow_status = Game_flow_status.game_end
                try:
                    if hasattr(self, 'chatbotWidget') and hasattr(self.chatbotWidget, 'add_system_bot_message'):
                        self.chatbotWidget.add_system_bot_message("Resigned the current game.")
                        self.chatbotWidget.add_system_bot_message("Press Tab to select the next option.")
                except Exception:
                    pass
                speak(t(Speak_template.user_resign.value))

                speak(t("speak.common.press_tab_next_option"))
                self.getOpponentMoveTimer.stop()
                self.getScoreTimer.start(1000)
                return

            if (
                self.userLoginName == None
                or self.game_play_mode == Game_play_mode.computer_mode
            ):
                self.clickWebButton(
                    [
                    ("#board-layout-sidebar > div > div.play-controller-component.sidebar-controller-component > div:nth-child(4) > div > div.primary-controls-topControls > button:nth-child(1)", "resign", False),
                    ("#board-layout-sidebar > div > div.play-controller-component.sidebar-controller-component > div:nth-child(4) > div > div.primary-controls-topControls > dialog > div > div > div.cc-confirmation-modal-buttons > button.cc-button-component.cc-button-danger.cc-button-large.cc-bg-danger", "resign", True),
                    ],
                    0,
                    callBack,
                    0,
                )
            else:
                self.clickWebButton(
                    [
                    ("#board-layout-sidebar > div > div.play-controller-component.sidebar-controller-component > div:nth-child(4) > div > div.primary-controls-topControls > button:nth-child(1)", "resign", False),
                    ("#board-layout-sidebar > div > div.play-controller-component.sidebar-controller-component > div:nth-child(4) > div > div.primary-controls-topControls > dialog > div > div > div.cc-confirmation-modal-buttons > button.cc-button-component.cc-button-danger.cc-button-large.cc-bg-danger", "resign", True),
                    ],
                    0,
                    callBack,
                    0,
                )
        else:
            speak(t("speak.common.cancel"))

    ##handle check position query, user input square name or piece type to check the location
    def check_position_handler(self):
        input = self.rightWidget.check_position.text().lower()
        print(any(char.isdigit() for char in input))
        if any(char.isdigit() for char in input):
            grid = input
            piece = self.chessBoard.check_grid(grid).__str__()
            speak_sentence = grid.upper()

            print(piece)
            if not piece == "Invalid square name":
                if not piece == "None":
                    if piece.__str__().islower():
                        speak_sentence = speak_sentence + " BLACK "
                    else:
                        speak_sentence = speak_sentence + " WHITE "
                    message = speak_sentence + PIECE_TYPE_CONVERSION[piece.__str__().lower()]
                    speak(message)
                    QMessageBox.information(self, "Position", message)
                else:
                    message = speak_sentence + " empty"
                    speak(message)
                    QMessageBox.information(self, "Position", message)
            else:
                speak(speak_sentence)
                QMessageBox.information(self, "Position", speak_sentence)
            self.rightWidget.check_position.clear()
            return
        else:
            piece_type = input
            try:
                piece_type = PIECE_TYPE_CONVERSION[piece_type]
            except Exception as e:
                print(e)
            grid = self.chessBoard.check_piece(piece_type)
            speak_string = ""
            white = grid["WHITE"]
            if len(white) > 0:
                speak_string = (
                    speak_string
                    + len(white).__str__()
                    + " WHITE "
                    + piece_type
                    + white.__str__().upper()
                )
            else:
                speak_string = speak_string + "NO WHITE " + piece_type + "found "

            speak_string = speak_string + " and "
            black = grid["BLACK"]
            if len(black) > 0:
                speak_string = (
                    speak_string
                    + len(black).__str__()
                    + " BLACK "
                    + piece_type
                    + black.__str__().upper()
                )
            else:
                speak_string = speak_string + "NO BLACK " + piece_type + "found "
            speak(speak_string)
  
            def list_to_str(lst):
                try:
                    return ", ".join([x.upper() for x in lst]) if isinstance(lst, list) else str(lst)
                except:
                    return str(lst)
            white_text = list_to_str(white)
            black_text = list_to_str(black)
            popup_text = f"WHITE {piece_type}: {white_text}\nBLACK {piece_type}: {black_text}"
            QMessageBox.information(self, "Position", popup_text)
            self.rightWidget.check_position.clear()
            return

    #focus on grid or keyboard-based interface
    def focus_back(self):
     
            try:
                if getattr(self, "_prefer_chatbot_focus", False):
                    if hasattr(self, 'chatbotWidget') and hasattr(self.chatbotWidget, 'message_input'):
                        self.chatbotWidget.message_input.setFocus()
                        return
            except:
                pass
            if self.input_mode == Input_mode.arrow_mode:
                self.leftWidget.grids[self.col][self.row].setFocus()
            else:
                self.rightWidget.commandPanel.setFocus()
            return
    
    ## interpret the input command and perform different task accordingly
    def CommandPanelHandler(self):

        input = self.rightWidget.commandPanel.text().lower()

        if input.count("computer") or input == "c":
            self.playWithComputerHandler()
            self.rightWidget.commandPanel.clear()
            return
        elif input.count("online") or input == "o":
            self.playWithOtherButtonHandler()
            self.rightWidget.commandPanel.clear()
            return
        if self.game_play_mode == Game_play_mode.puzzle_mode:
            self._execute_user_move(input, source="command_panel")
            self.rightWidget.commandPanel.clear()
            return
        
        match self.main_flow_status:

            case Bot_flow_status.select_status:
                if input.count("+"):
                    minute = input.split("+")[0]
                    increment = input.split("+")[1]
                    print(f"minute = {minute}, inc = {increment}")

            case Bot_flow_status.board_init_status:
                return
            case Bot_flow_status.game_play_status:
                if input.count("color"):
                    speak("You are playing as {}".format(self.userColor))
                    return
                if input.count("time") or input == "t":
                    if self.game_play_mode == Game_play_mode.online_mode:

                        def timeCallback(clocks):
                            if not clocks == None:
                                user_time = clocks[1].split(":")
                                user = (
                                    user_time[0]
                                    + " minutes "
                                    + user_time[1]
                                    + " seconds"
                                )

                                opponent_time = clocks[0].split(":")
                                opponent = (
                                    opponent_time[0]
                                    + " minutes "
                                    + opponent_time[1]
                                    + " seconds"
                                )
                                speak(
                                    t(
                                        Speak_template.check_time_sentense.value,
                                        user=user,
                                        opponent=opponent,
                                    )
                                )

                        self.leftWidget.checkTime(timeCallback)
                        self.rightWidget.commandPanel.clear()
                        return
                    else:
                        speak(t("speak.game.no_timer_computer_mode"))
                        self.rightWidget.commandPanel.clear()
                        return
                if input.count("resign"):
                    self.resign_handler()
                    self.rightWidget.commandPanel.clear()
                    return
                if input.count("where"):
                    piece_type = input.replace("where", "").replace(" ", "")
                    try:
                        piece_type = PIECE_TYPE_CONVERSION[piece_type]
                    except Exception as e:
                        print(e)
                    grid = self.chessBoard.check_piece(piece_type)
                    speak_string = ""
                    white = grid["WHITE"]
                    if len(white) > 0:
                        speak_string = (
                            speak_string
                            + len(white).__str__()
                            + " WHITE "
                            + piece_type
                            + white.__str__().upper()
                        )
                    else:
                        speak_string = speak_string + "NO WHITE " + piece_type

                    speak_string = speak_string + " and "
                    black = grid["BLACK"]
                    if len(white) > 0:
                        speak_string = (
                            speak_string
                            + len(black).__str__()
                            + " BLACK "
                            + piece_type
                            + black.__str__().upper()
                        )
                    else:
                        speak_string = speak_string + "NO BLACK " + piece_type
                    # speak(piece_type + " " + grid.__str__())
                    speak(speak_string)
                    self.rightWidget.commandPanel.clear()
                    return
                elif input.count("what"):
                    grid = input.replace("what", "").replace(" ", "")
                    piece = self.chessBoard.check_grid(grid).__str__()
                    speak_sentence = grid.upper()

                    print(piece)
                    if not piece == "Invalid square name":
                        if not piece == "None":
                            if piece.__str__().islower():
                                speak_sentence = speak_sentence + " BLACK "
                            else:
                                speak_sentence = speak_sentence + " WHITE "
                            speak(
                                speak_sentence
                                + PIECE_TYPE_CONVERSION[piece.__str__().lower()]
                            )
                        else:
                            speak(speak_sentence + " empty")
                    else:
                        speak(speak_sentence)
                    self.rightWidget.commandPanel.clear()
                    return
                self._execute_user_move(input, source="command_panel")

    def _append_chatbot_system_message(self, message: str):

        if not message:
            return
        try:
            if hasattr(self, "chatbotWidget") and hasattr(self.chatbotWidget, "chat_display"):
                line = t("chat.bot_line", message=message)
                self.chatbotWidget.chat_display.append(line)
        except Exception:

            pass
    def _execute_user_move(self, move_text: str, source: str = ""):
        """統一聊天框 / command panel / 語音的走子入口。"""
        raw_move = (move_text or "").strip()
        if not raw_move:
            return


        if re.fullmatch(r"[A-Ha-h][1-8][A-Ha-h][1-8][QRBNqrbn]?", raw_move):
            move_text = raw_move.lower()
        else:
            move_text = raw_move

        if self.chessBoard is None or getattr(self.chessBoard, "board_object", None) is None:
            msg = "No active game board detected. Please start or load a game before making moves."
            speak(msg)
            self._append_chatbot_system_message(msg)
            return

        if self.game_play_mode != Game_play_mode.puzzle_mode:
            if self.game_flow_status != Game_flow_status.user_turn:
                speak(t("speak.game.wait_opponent_move"))
                self._append_chatbot_system_message("Please wait for your opponent's move")
                return

        if self.game_play_mode == Game_play_mode.puzzle_mode:
            self.puzzle_movePiece(move_text)
        else:
            self.movePiece(move_text)

    def movePiece(self, input):  ## input store the move command
        if self.game_play_mode == Game_play_mode.online_mode and not self.online_game_started:
            speak(t("speak.game.not_started_wait_matchmaking"))
            self.rightWidget.commandPanel.clear()
            return

        movePair = self.chessBoard.moveWithValidate(input)
        # check_win = self.chessBoard.detect_win()

        print(self.chessBoard.board_object)
        san_string = ""
        uci_string = ""
        human_string = ""
        if len(movePair) == 2:
            uci_string = movePair[0]
            san_string = movePair[1]
            human_string = self.move_to_human_form(
                self.userColor, uci_string, san_string
            )

            # movePair = movePair[0]

        if len(uci_string) == 5:

            target_col = int(CHESSBOARD_LOCATION_CONVERSION[uci_string[0].lower()]) - 1 
            target_row = int(uci_string[1]) - 1
            dest_col = int(CHESSBOARD_LOCATION_CONVERSION[uci_string[2].lower()]) - 1   #index
            dest_row = int(uci_string[3]) - 1
            dest = uci_string[2:4]
            print(f"dest_row: {dest_row}, dest_col: {dest_col}")
            promoteTo = uci_string[4].lower()
            promote_index = list(PIECE_TYPE_CONVERSION).index(promoteTo)

            print(f"promote_index: {promote_index}")

            # dlg = confirmMoveDialog("pawn", dest, promote=promoteTo)
            dlg = confirmDialog(human_string)
            if dlg.exec():
                self.all_grids_switch(False)
                targetWidget = self.leftWidget.grids[target_col][target_row]
                destWidget = self.leftWidget.grids[dest_col][dest_row]
                if widgetDragDrop(targetWidget, destWidget):
                    match self.userColor:
                        case "BLACK":
                            promoteRow = dest_row + promote_index
                        case "WHITE":
                            promoteRow =  dest_row - promote_index
                    print(f"dest_col: {dest_col}, promoteRow: {promoteRow}")
                    promoteWidget = self.leftWidget.grids[dest_col][promoteRow]
                    if widgetClick(promoteWidget):
                        self.rightWidget.commandPanel.clear()
                        QTimer.singleShot(1000, self.focus_back)
                        self.setMoveList(uci_string)

 
                        check_win = self.chessBoard.detect_win()
                        if check_win != t("chess.win.none"):
                            print(check_win)
                            speak(check_win, announce=True)
                            self.game_flow_status = Game_flow_status.game_end
                            self.change_main_flow_status(Bot_flow_status.game_end_status)
                            self.getOpponentMoveTimer.stop()
                            self.getScoreTimer.start(1000)
                        else:
                            self.getOpponentMoveTimer.start(1000)
            else:
                self.chessBoard.board_object.pop()
                self.rightWidget.commandPanel.clear()
                self.game_flow_status = Game_flow_status.user_turn
                try:
                    self._latest_web_fen = None
                    self._latest_web_fen_time = 0
                    self._refresh_fen_from_web(reason="cancel_move")
                except Exception:
                    pass
                print("Cancel!")

        elif len(uci_string) == 4:

            target_col = int(CHESSBOARD_LOCATION_CONVERSION[uci_string[0].lower()]) - 1
            target_row = int(uci_string[1]) - 1
            dest_col = int(CHESSBOARD_LOCATION_CONVERSION[uci_string[2].lower()]) - 1
            dest_row = int(uci_string[3]) - 1
            dest = uci_string[2:4]
            target_type = PIECE_TYPE_CONVERSION.get(
                self.chessBoard.check_grid(dest).__str__().lower()
            )
            # dlg = confirmMoveDialog(target_type, dest)
            dlg = confirmDialog(human_string)
            if dlg.exec():
                self.all_grids_switch(False)
                # QTimer.singleShot(3000, partial(self.clickStart,input))
                # print(self.chessBoard.board_object)

                targetWidget = self.leftWidget.grids[target_col][target_row]
                destWidget = self.leftWidget.grids[dest_col][dest_row]
                self.rightWidget.commandPanel.clear()
                if widgetDragDrop(targetWidget, destWidget):
                    QTimer.singleShot(1000, self.focus_back)
                    self.setMoveList(uci_string)

              
                    check_win = self.chessBoard.detect_win()
                    if check_win != t("chess.win.none"):
                        print(check_win)
                        speak(check_win, announce=True)
                        self.game_flow_status = Game_flow_status.game_end
                        self.change_main_flow_status(Bot_flow_status.game_end_status)
                        self.getOpponentMoveTimer.stop()
                        self.getScoreTimer.start(1000)
                    else:
                        self.getOpponentMoveTimer.start(1000)

            else:
                self.chessBoard.board_object.pop()
                self.rightWidget.commandPanel.clear()
                self.game_flow_status = Game_flow_status.user_turn
                try:
                    self._latest_web_fen = None
                    self._latest_web_fen_time = 0
                    self._refresh_fen_from_web(reason="cancel_move")
                except Exception:
                    pass
                print("Cancel!")
        elif movePair == "Promotion":
            print("Promotion")
            speak(
                "Please indicate the promotion piece by typing the first letter"
            )
            self.rightWidget.commandPanel.setFocus()
        else:
            error_text = input + movePair
            speak(error_text)
            print(error_text)  ##error move speak
            self._append_chatbot_system_message(error_text)
            self.rightWidget.commandPanel.clear()
        
        QTimer.singleShot(500, lambda: self.runJavaScriptSafe(js_function.getPiecesLocation, self.getPiecesLocation))

    ##check game end, sync with mirrored chess board and announce opponent's move
    def announceMove(self, sanString):
        print("broadcast move: ", sanString)
        if sanString == None or self.chessBoard == None:
            return False
        crawl_result = None
        check_win = self.chessBoard.detect_win()
        if check_win != t("chess.win.none"):  ##check user wins
            print(check_win)
            speak(check_win, announce=True)
            self.game_flow_status = Game_flow_status.game_end
            self.change_main_flow_status(Bot_flow_status.game_end_status)
            self.getOpponentMoveTimer.stop()
            self.getScoreTimer.start(1000)

            return True
        
        print("check none ")
        if sanString != None:
            print(sanString)
            movePair = self.chessBoard.moveWithValidate(sanString)
            if not len(movePair) == 2:
                if not crawl_result == None:
                    self.game_flow_status = Game_flow_status.game_end
                    self.change_main_flow_status(Bot_flow_status.game_end_status)
                    self.getOpponentMoveTimer.stop()
                    self.getScoreTimer.start(1000)
                    speak(crawl_result, True, announce=True)
                    return True
                else:
                    return False
            uci_string = movePair[0]
            san_string = movePair[1]


            try:
                last_move = self.chessBoard.board_object.peek()
                moved_piece = self.chessBoard.board_object.piece_at(last_move.to_square)
                expected_opponent_color = chess.WHITE if self.opponentColor == "WHITE" else chess.BLACK
                if moved_piece is None or moved_piece.color != expected_opponent_color:
                
                    self.chessBoard.board_object.pop()
                    return False
            except Exception:
                pass

            print(self.chessBoard.board_object)
            if len(uci_string) <= 5:
                human_string = self.move_to_human_form(
                    self.opponentColor, uci_string, san_string
                )

                check_win = self.chessBoard.detect_win()
                print(check_win)
                print(crawl_result)
                speak(
                    human_string,
                    True,
                    announce=True,
                )
                self.rightWidget.opponentBox.setText(
                    f"{t('ui.opponent_last_move')} {human_string}"
                )
                self.game_flow_status = Game_flow_status.user_turn
                if check_win != t("chess.win.none"):
                    speak(check_win, True, announce=True)
                    self.game_flow_status = Game_flow_status.game_end
                    self.change_main_flow_status(Bot_flow_status.game_end_status)
                    self.getOpponentMoveTimer.stop()
                    self.getScoreTimer.start(1000)
                if not crawl_result == None:
                    self.game_flow_status = Game_flow_status.game_end
                    self.change_main_flow_status(Bot_flow_status.game_end_status)
                    self.getOpponentMoveTimer.stop()
                    self.getScoreTimer.start(1000)
                    speak(crawl_result, True, announce=True)
                return True
        
        return False

    def announce_current_status(self):
        try:
            color_text = "You are playing as white" if self.userColor == "WHITE" else "You are playing as black"
            turn_text = "Your turn" if self.game_flow_status == Game_flow_status.user_turn else "Opponent's turn"
            last_move_text = self.rightWidget.opponentBox.text()
            white_text = self.rightWidget.whitePieces.text()
            black_text = self.rightWidget.blackPieces.text()
            speak(f"{color_text}. {turn_text}. {white_text}. {black_text}. {last_move_text}")
        except:
            pass

    

    ##Check whether opponent resigned
    def check_game_end(self):

        if getattr(self, "main_flow_status", None) != Bot_flow_status.game_play_status:
            return

        page = None
        try:
            page = self.leftWidget.chessWebView.page()
        except Exception:
            page = None
        if page is None:
            return

        def callback(result):
            if not result:
                return
            self.game_flow_status = Game_flow_status.game_end
            self.change_main_flow_status(Bot_flow_status.game_end_status)
            self.getScoreTimer.start(1000)
            self.getOpponentMoveTimer.stop()
            print(result)
            speak(result, announce=True)

        mode = "computer" if self.game_play_mode == Game_play_mode.computer_mode else "online"
        try:
            self.runJavaScriptSafe(js_function.checkGameEnd + f'checkGameEnd("{mode}");', callback)
        except Exception:
            return

    ##JS to get opponent move SAN
    def getOpponentMove(self):
        if self.main_flow_status != Bot_flow_status.game_play_status:
            self.getOpponentMoveTimer.stop()
            return
        if self.game_play_mode == Game_play_mode.online_mode and not self.online_game_started:
            self.getOpponentMoveTimer.stop()
            return

        def callback(x):
            san_move = None
            row_sig = ""


            try:
                if isinstance(x, (list, tuple)):
                    san_move = x[0] if len(x) > 0 else None
                    row_sig = str(x[1]) if len(x) > 1 and x[1] is not None else ""
                else:
                    san_move = x
            except Exception:
                san_move = x

            print(f"Opponent move = {san_move}")

            if self.main_flow_status != Bot_flow_status.game_play_status:
                self.getOpponentMoveTimer.stop()
                return
            if self.game_play_mode == Game_play_mode.online_mode and not self.online_game_started:
                self.getOpponentMoveTimer.stop()
                return


            if row_sig and row_sig == getattr(self, "_last_opponent_row_sig", ""):
                if self.game_flow_status == Game_flow_status.opponent_turn:
                    self.getOpponentMoveTimer.start(1000)
                return

            if self.announceMove(san_move):
                self.getOpponentMoveTimer.stop()
                if row_sig:
                    self._last_opponent_row_sig = row_sig
                try:
                    if len(self.chessBoard.board_object.move_stack) == 0:
                        return
                    move = self.chessBoard.board_object.pop()
                    self.setMoveList(move)
                    self.chessBoard.board_object.push_uci(str(move))
                except Exception:
                    return
                self.runJavaScriptSafe(js_function.getPiecesLocation, self.getPiecesLocation)
       
                QTimer.singleShot(600, lambda: self._refresh_fen_from_web(reason="opponent_move"))
            elif self.game_flow_status == Game_flow_status.opponent_turn:
                self.getOpponentMoveTimer.start(1000)

        if(self.userColor=="WHITE"):
            jsCode = js_function.white_GetOpponentMove
        else:
            jsCode = js_function.black_GetOpponentMove
        if self.input_mode == Input_mode.arrow_mode:
            self.all_grids_switch(True)

        self.game_flow_status = Game_flow_status.opponent_turn

        self.runJavaScriptSafe(jsCode, callback)

    def _refresh_fen_from_web(self, reason: str = ""):

        if not getattr(self, "enable_share_fen_sync", False):
            return

        try:
            if getattr(self, "main_flow_status", None) != Bot_flow_status.game_play_status:
                return
            if getattr(self, "chessBoard", None) is None or getattr(self.chessBoard, "board_object", None) is None:
                return
        except Exception:
            return

        page = None
        try:
            page = self.leftWidget.chessWebView.page()
        except Exception:
            page = None
        if page is None:
            return

        def _apply_fen(fen_value):
            if not fen_value or not isinstance(fen_value, str):
                return
            fen_value = fen_value.strip()

            if len(fen_value.split()) < 4:
                return
            try:
                self.chessBoard.board_object = chess.Board(fen_value)
                self._latest_web_fen = fen_value
                self._latest_web_fen_time = time.time()
                print(f"[FEN sync]{'['+reason+']' if reason else ''} {fen_value}")
            except Exception as exc:
                print(f"Web FEN sync failed: {exc}")

        def _try_read_fen(retry_count=0):
            def _on_fen(fen_value):
          
                if (not fen_value or fen_value is False) and retry_count < 8:
                    QTimer.singleShot(180, lambda: _try_read_fen(retry_count + 1))
                    return
                _apply_fen(fen_value)
            self.runJavaScriptSafe(js_function.getFEN, _on_fen)

        def _after_share(clicked_ok):
     
            if not clicked_ok:
                try:
                    self.runJavaScriptSafe(js_function.clickShare)
                except Exception:
                    pass
      
            QTimer.singleShot(280, lambda: _try_read_fen(0))

        try:
            self.runJavaScriptSafe(js_function.clickShare, _after_share)
        except Exception:
       
            return



    def open_online_category_page(self):

        self.current_timecontrol_category = None
        self.current_timecontrol_options = []
        self.selected_time_control_name = None
        try:
            if hasattr(self.rightWidget, "online_category_group"):
                self.rightWidget.online_category_group.setExclusive(False)
                for btn in self.rightWidget.online_category_buttons.values():
                    btn.setChecked(False)
                self.rightWidget.online_category_group.setExclusive(True)
        except Exception:
            pass


        try:
            self.clickWebButton(
                [
                    (
                        "#board-layout-sidebar > div.sidebar-content > div.new-game-component > div.new-game-primary > div > button",
                        "",
                    ),
                    (
                        "#board-layout-sidebar > div.sidebar-content > div.new-game-component > div.new-game-primary > div > div:nth-child(4) > div.toggle-custom-game-component > button",
                        "",
                    ),
                ],
                0,
                lambda: None,
                0,
            )
        except Exception:
            pass


        for widget in self.rightWidget.online_mode_select_menu:
            widget.hide()

        for item in self.rightWidget.bot_category_select_menu:
            item.hide()
        for scroll in self.rightWidget.bot_category_lists.values():
            scroll.hide()

        for btn in self.rightWidget.online_category_buttons.values():
            btn.setChecked(False)
            btn.show()

        self.rightWidget.online_start_game_button.hide()
        self.rightWidget.back_to_previous_page_button.hide()
        self.rightWidget.returnToHomePageButton.show()


        self.currentFocus = -1
        try:
            first_btn = next(iter(self.rightWidget.online_category_buttons.values()), None)
            if first_btn:
                first_btn.setFocus()
        except Exception:
            pass
        try:
            speak(t("speak.game.select_time_control_category"))
        except Exception:
            pass

    def open_online_selection_page(self, category: str):

        self.current_timecontrol_category = category
        self.current_timecontrol_options = self.time_control_by_category.get(category, [])
        self.selected_time_control_name = None
        try:
            if hasattr(self.rightWidget, "online_selection_group"):
                self.rightWidget.online_selection_group.setExclusive(False)
                for btn in self.rightWidget.online_selection_buttons:
                    btn.setChecked(False)
                self.rightWidget.online_selection_group.setExclusive(True)
        except Exception:
            pass


        for widget in self.rightWidget.online_mode_select_menu:
            widget.hide()


        for item in self.rightWidget.bot_category_select_menu:
            item.hide()
        for scroll in self.rightWidget.bot_category_lists.values():
            scroll.hide()


        for idx, btn in enumerate(self.rightWidget.online_selection_buttons):
            if idx < len(self.current_timecontrol_options):
                option = self.current_timecontrol_options[idx]
                btn.setText(option["name"])
                btn.setChecked(False)
                btn.show()
            else:
                btn.setChecked(False)
                btn.hide()


        self.rightWidget.back_to_previous_page_button.show()
        self.rightWidget.online_start_game_button.setEnabled(False)
        self.rightWidget.online_start_game_button.show()
        self.rightWidget.returnToHomePageButton.show()

        self.currentFocus = -1
        try:
            if self.rightWidget.online_selection_buttons:
                for btn in self.rightWidget.online_selection_buttons:
                    if btn.isVisible():
                        btn.setFocus()
                        break
        except Exception:
            pass
        try:
            speak(t("speak.game.select_category_time_control", category=category))
        except Exception:
            pass

    def handle_online_selection_button(self, index: int):
        if not self.current_timecontrol_options:
            return
        if index < 0 or index >= len(self.current_timecontrol_options):
            return

        option = self.current_timecontrol_options[index]
        self.selected_time_control_name = option["name"]
        for idx, btn in enumerate(self.rightWidget.online_selection_buttons):
            if idx == index:
                btn.setChecked(True)
            else:
                btn.setChecked(False)
        self.rightWidget.online_start_game_button.setEnabled(True)

        try:
            speak(t("speak.game.time_control_selected", name=self.selected_time_control_name))
        except Exception:
            pass

    def start_online_game(self):
        if not self.selected_time_control_name:
            return

        self.online_select_timeControl(self.selected_time_control_name)

    ##initialize mirror chessboard
    def getBoard(self, *args):
        self.chessBoard = ChessBoard(args[0]) if(args) else ChessBoard()
        self.change_main_flow_status(Bot_flow_status.game_play_status)

    ##toggle the marked square layer -> hide before perfrom click
    def all_grids_switch(self, on_off):
        for i in range(8):
            for j in range(8):
                if on_off:
                    self.leftWidget.grids[i][j].show()
                else:
                    self.leftWidget.grids[i][j].hide()

    ##JS to detect the assigned color
        
    def getColor(self, exist_game = ""):
        def callback(color):
            print(color)

            if color is None:
                QTimer.singleShot(500, lambda: self.getColor(exist_game))
                return

            color = str(color)
            self.userColor = color
            self.rightWidget.colorBox.setText(f"{t('ui.assigned_color')} {color}")
            if color == "BLACK":
                self.opponentColor = "WHITE"
                self.row, self.col = 7, 7
                self.currentPos = 'h8'
                speak(exist_game + t(Speak_template.user_black_side_sentense.value))
                QTimer.singleShot(150, lambda: self.runJavaScriptSafe(js_function.getPiecesLocation, self.getPiecesLocation))
                self.game_flow_status = Game_flow_status.opponent_turn
                self.getOpponentMoveTimer.start(1000)
            else:
                self.opponentColor = "BLACK"
                self.row, self.col = 0, 0
                self.currentPos = 'a1'
                speak(exist_game + t(Speak_template.user_white_side_sentense.value))
                QTimer.singleShot(150, lambda: self.runJavaScriptSafe(js_function.getPiecesLocation, self.getPiecesLocation))
                self.game_flow_status = Game_flow_status.user_turn

        self.runJavaScriptSafe(js_function.getColor, callback)

    #JS to detect grid position and assign label reference
    def initBoard(self):
        def callback(coor):
            print(coor)
            if not coor or len(coor) < 3:
                print('getBoard returned invalid coor:', coor)
                return
            left = float(coor[0])
            top = float(coor[1])
            square = float(coor[2])
            dist = square
            # store base board metrics for later repositioning
            self.board_base_left = left
            self.board_base_top = top
            self.board_base_square = square
            scale = float(self.leftWidget.chessWebView.zoomFactor())
            web_tl = self.leftWidget.chessWebView.mapTo(self, QPoint(0, 0))
            print(f"INITBOARD COLOR: {self.userColor}")
            if(self.userColor == "WHITE"):
                for row in range(8):
                    for col in range(8):
                        label = QLabel(self)
                        # row=0 is a1 (bottom). top + (7-row)*square gives y coordinate for that row
                        lx = int(web_tl.x() + (left + col * square) * scale)
                        ly = int(web_tl.y() + (top + (7 - row) * square) * scale)
                        size = max(1, int(square * scale))
                        label.setGeometry(lx, ly, size, size)
                        pos = list(CHESSBOARD_LOCATION_CONVERSION.keys())[list(CHESSBOARD_LOCATION_CONVERSION.values()).index(str(col+1))] + str(row+1)
                        label.setAccessibleName(pos)
                        label.hide()
                        self.leftWidget.grids[col][row] = label
            else:
                for row in range(8):
                    for col in range(8):
                        label = QLabel(self)
                        # black orientation: flip cols and rows
                        lx = int(web_tl.x() + (left + (7 - col) * square) * scale)
                        ly = int(web_tl.y() + (top + row * square) * scale)
                        size = max(1, int(square * scale))
                        label.setGeometry(lx, ly, size, size)
                        pos = list(CHESSBOARD_LOCATION_CONVERSION.keys())[list(CHESSBOARD_LOCATION_CONVERSION.values()).index(str(col+1))] + str(row+1)
                        label.setAccessibleName(pos)
                        label.hide()
                        self.leftWidget.grids[col][row] = label

            self.runJavaScriptSafe(js_function.getPiecesLocation, self.getPiecesLocation)

        # after initial board detection, ensure grids are repositioned when window resizes

        self.runJavaScriptSafe(js_function.getBoard, callback)

    def update_board_base(self, coor):
        """Update stored base board coordinates from JS and reposition grids.

        This method can be called repeatedly (e.g., after window resize)
        to refresh the mapping between page coordinates and overlay labels.
        """
        try:
            if not coor or len(coor) < 3:
                return
            left = float(coor[0])
            top = float(coor[1])
            square = float(coor[2])
            self.board_base_left = left
            self.board_base_top = top
            self.board_base_square = square
            QTimer.singleShot(50, self.reposition_grids)
        except Exception:
            pass

    def reposition_grids(self):
        """Recompute and set QLabel geometries for grid overlays according to current zoom and webview position."""
        try:
            if not hasattr(self, 'board_base_left'):
                return
            scale = float(self.leftWidget.chessWebView.zoomFactor())
            base_left = float(self.board_base_left)
            base_top = float(self.board_base_top)
            base_square = float(self.board_base_square)

            # webview top-left in main window coordinates
            web_tl_global = self.leftWidget.chessWebView.mapToGlobal(QPoint(0,0))
            web_tl = self.mapFromGlobal(web_tl_global)

            if self.userColor == 'WHITE':
                for row in range(8):
                    for col in range(8):
                        label = self.leftWidget.grids[col][row]
                        if not label:
                            continue
                        lx = int(web_tl.x() + (base_left + col * base_square) * scale)
                        ly = int(web_tl.y() + (base_top + (7 - row) * base_square) * scale)
                        size = max(1, int(base_square * scale))
                        label.setGeometry(lx, ly, size, size)
            else:
                for row in range(8):
                    for col in range(8):
                        label = self.leftWidget.grids[col][row]
                        if not label:
                            continue
                        lx = int(web_tl.x() + (base_left + (7 - col) * base_square) * scale)
                        ly = int(web_tl.y() + (base_top + row * base_square) * scale)
                        size = max(1, int(base_square * scale))
                        label.setGeometry(lx, ly, size, size)
        except Exception:
            pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # when main window resizes, refresh board coords from webview and update overlays
        QTimer.singleShot(80, lambda: self.runJavaScriptSafe(js_function.getBoard, self.update_board_base))

    ##switch to command mode
    def switch_command_mode(self):
        print("shortcut ctrl + F pressed")
        speak(t("speak.mode.command_mode_hint"))
        self.arrow_mode_switch(False)
        self.input_mode = Input_mode.command_mode
        self.currentFocus = len(self.rightWidget.play_menu) - 1
        self.rightWidget.commandPanel.setFocus()

    ##switch to arrow mode, only allowd when game started
    def switch_arrow_mode(self):
        print("shortcut ctrl + J pressed")
        if self.main_flow_status == Bot_flow_status.game_play_status:

            speak(t("speak.mode.arrow_mode"))
            self.input_mode = Input_mode.arrow_mode
            self.arrow_mode_switch(True)
            self.all_grids_switch(True)
            self.rightWidget.commandPanel.clear()

            self.setStyleSheet(
                "QLabel:focus { border: 5px solid rgba(255, 0, 0, 1); }"
            )

            self.leftWidget.grids[self.col][self.row].setFocus()

    ##arrow key move and speak the square information
    def handle_arrow(self, direction):
        if not self.main_flow_status == Bot_flow_status.game_play_status:
            return
        # print(self.currentFocus, direction)
        print(f"col: {self.col}, row: {self.row}")
        match direction:
            case 'UP':
                if(self.userColor == "WHITE"):
                    self.row = min(self.row + 1, 7)
                    self.leftWidget.grids[self.col][self.row].setFocus()
                else:
                    self.row = max(self.row - 1, 0)
                    self.leftWidget.grids[self.col][self.row].setFocus()
    
            case 'DOWN':
                if(self.userColor == "WHITE"):
                    self.row = max(self.row - 1, 0)
                    self.leftWidget.grids[self.col][self.row].setFocus()
                else:
                    self.row = min(self.row + 1, 7)
                    self.leftWidget.grids[self.col][self.row].setFocus()

            case 'RIGHT':
                if(self.userColor == "WHITE"):
                    self.col = min(self.col + 1, 7)
                    self.leftWidget.grids[self.col][self.row].setFocus()
                else:
                    self.col = max(self.col - 1, 0)
                    self.leftWidget.grids[self.col][self.row].setFocus()

            case 'LEFT':
                if(self.userColor == "WHITE"):
                    self.col = max(self.col - 1, 0)
                    self.leftWidget.grids[self.col][self.row].setFocus()
                else:
                    self.col = min(self.col + 1, 7)
                    self.leftWidget.grids[self.col][self.row].setFocus()
        # QLabel.setAccessibleDescription("HELLO")
        # QLabel.setAccessibleName("Name")
        self.currentPos = list(CHESSBOARD_LOCATION_CONVERSION.keys())[list(CHESSBOARD_LOCATION_CONVERSION.values()).index(str(self.col+1))] + str(self.row+1)
        piece = self.chessBoard.check_grid(self.currentPos).__str__()
        if piece == "None":
            self.leftWidget.grids[self.col][self.row].setAccessibleName(self.currentPos)
            speak("{0}".format(self.currentPos))
            return
        else:
            color = "white" if piece.isupper() else "black"
            piece_square_text = "{0} {1} {2}".format(
                self.currentPos,
                color,
                PIECE_TYPE_CONVERSION.get(piece.lower()),
            )
            self.leftWidget.grids[self.col][self.row].setAccessibleName(piece_square_text)
            print(piece_square_text)
            speak(piece_square_text)

    ##select the piece under arrow mode
    def handle_space(self):
        if not self.input_mode == Input_mode.arrow_mode:
            return
        if len(self.rightWidget.commandPanel.text()) == 4:
            self.CommandPanelHandler()
            return
        if not self.currentPos == None:
            piece = self.chessBoard.check_grid(self.currentPos).__str__()
            if not piece == "None":
                color = "white" if piece.isupper() else "black"
                piece = PIECE_TYPE_CONVERSION.get(piece.lower())
                speak(color + " " + piece + " selected")

        current_value = self.rightWidget.commandPanel.text()
        self.rightWidget.commandPanel.setText(current_value + self.currentPos)
        if len(self.rightWidget.commandPanel.text()) == 4:
            self.CommandPanelHandler()

    ##clear the selected piece under arrow mode
    def handle_arrow_delete(self):
        if not self.input_mode == Input_mode.arrow_mode:
            return
        self.rightWidget.commandPanel.setText("")

    ##control tab event on right widget
    def handle_tab(self, press):
        if self.input_mode == Input_mode.command_mode:
            if self.game_play_mode == Game_play_mode.analysis_mode:
                unhidden_widgets = [w for w in self.rightWidget.analysis_menu if w.isVisible()]
            elif self.main_flow_status == Bot_flow_status.login_status:
                unhidden_widgets = [w for w in self.rightWidget.login_menu if w.isVisible()]
            elif self.main_flow_status == Bot_flow_status.setting_status:
                unhidden_widgets = [w for w in self.rightWidget.setting_menu if w.isVisible()]
            elif self.main_flow_status == Bot_flow_status.select_status:
                if self.game_play_mode == Game_play_mode.online_mode:
                    unhidden_widgets = [w for w in self.rightWidget.online_mode_select_menu if w.isVisible()]
                elif self.game_play_mode == Game_play_mode.computer_mode:

                    active_list = None
                    active_buttons = []
                    if getattr(self, "selected_bot_category", None):
                        active_list = self.rightWidget.bot_category_lists.get(self.selected_bot_category)
                        active_buttons = self.rightWidget.bot_category_buttons.get(self.selected_bot_category, [])
                    if active_list is not None and active_list.isVisible():
                        unhidden_widgets = [w for w in active_buttons if w is not None and w.isVisible()]
                        # append action buttons at the end
                        for w in [self.rightWidget.back_to_category_button]:
                            if w is not None and w.isVisible():
                                unhidden_widgets.append(w)
                    else:
                        unhidden_widgets = [w for w in self.rightWidget.bot_category_select_menu if w.isVisible()]
                elif self.game_play_mode == Game_play_mode.puzzle_mode:
                    unhidden_widgets = [w for w in getattr(self.rightWidget, "puzzle_menu", []) if w.isVisible()]
                else:
                    unhidden_widgets = [w for w in self.rightWidget.setting_menu if w.isVisible()]
            elif self.main_flow_status == Bot_flow_status.game_play_status:
                unhidden_widgets = [w for w in self.rightWidget.play_menu if w.isVisible()]
            elif self.main_flow_status == Bot_flow_status.game_end_status:
                unhidden_widgets = [w for w in self.rightWidget.game_end_menu if w.isVisible()]
            elif self.main_flow_status == Bot_flow_status.puzzle_end_status:
                unhidden_widgets = [w for w in self.rightWidget.puzzle_end_menu if w.isVisible()]
            else:
                unhidden_widgets = [w for w in self.rightWidget.setting_menu if w.isVisible()]
            if not unhidden_widgets:
                print("No focusable widgets found")
                return
                
            print(f"Found {len(unhidden_widgets)} focusable widgets")
            
            current_focused = None
            if self.currentFocus < len(unhidden_widgets):
                current_focused = unhidden_widgets[self.currentFocus]
            
            from PyQt6.QtWidgets import QComboBox
            active_combobox = None
            if isinstance(current_focused, QComboBox):
                active_combobox = current_focused
            else:
                for widget in unhidden_widgets:
                    if isinstance(widget, QComboBox) and widget.view().isVisible():
                        active_combobox = widget
                        if widget in unhidden_widgets:
                            self.currentFocus = unhidden_widgets.index(widget)
                        break
            
            if active_combobox and press in ["UP", "DOWN"]:
                print(f"ComboBox focused, handling {press} key for option selection")
                if not active_combobox.view().isVisible():
                    active_combobox.showPopup()
                    QTimer.singleShot(50, lambda: None)
                
                current_index = active_combobox.currentIndex()
                if press == "UP":
                    if current_index > 0:
                        new_index = current_index - 1
                    else:
                        new_index = active_combobox.count() - 1
                else:  # DOWN
                    if current_index < active_combobox.count() - 1:
                        new_index = current_index + 1
                    else:
                        new_index = 0
                
                active_combobox.setCurrentIndex(new_index)
                active_combobox.highlighted.emit(new_index)
                
                try:
                    item_data = active_combobox.itemData(new_index, Qt.ItemDataRole.AccessibleTextRole)
                    if item_data:
                        speak(item_data)
                    else:
                        speak(active_combobox.itemText(new_index))
                except:
                    speak(active_combobox.itemText(new_index))
                
                return
            
            match press:
                case "UP" | "LEFT":
                    print("up")
                    if int(self.currentFocus - 1) < 0:
                        self.currentFocus = len(unhidden_widgets)-1
                    else:
                        self.currentFocus = self.currentFocus - 1
                case "DOWN" | "RIGHT":
                    print("down")
                    if int(self.currentFocus + 1) >= len(unhidden_widgets):
                        self.currentFocus = 0
                    else:
                        self.currentFocus = self.currentFocus + 1
                case "TAB":
                    print("tab")
                    if int(self.currentFocus + 1) >= len(unhidden_widgets):
                        self.currentFocus = 0
                    else:
                        self.currentFocus = self.currentFocus + 1

            if self.currentFocus >= len(unhidden_widgets):
                self.currentFocus = 0
            if self.currentFocus < 0:
                self.currentFocus = len(unhidden_widgets) - 1
                
            target_widget = unhidden_widgets[self.currentFocus]
            print(f"Setting focus to widget: {target_widget}, index: {self.currentFocus}")
            target_widget.setFocus()
            try:
                if hasattr(target_widget, "isCheckable") and target_widget.isCheckable():
                    target_widget.setChecked(True)
            except Exception:
                pass
            target = unhidden_widgets[self.currentFocus]
            intro = ""
            if hasattr(target, "text"):
                try:
                    intro = target.text()
                except Exception:
                    intro = ""
            if not intro and hasattr(target, "accessibleDescription"):
                intro = target.accessibleDescription() or ""
            from PyQt6.QtWidgets import QScrollArea
            if not intro and isinstance(target, QScrollArea):
                child = target.widget()
                if child and hasattr(child, "text"):
                    intro = child.text()
            if not intro and hasattr(target, "currentIndex"):
                try:
                    index = target.currentIndex()
                    intro = "Current Bot: " + str(
                        target.itemData(index, Qt.ItemDataRole.AccessibleTextRole)
                        or target.currentText()
                    )
                except Exception:
                    intro = intro or ""
            if not intro:
                intro = target.objectName() or target.__class__.__name__

            try:
                from PyQt6.QtWidgets import QPushButton
                if isinstance(target_widget, QPushButton) and getattr(self, "tts_thread", None):
                    sound_path = self._get_resource_path(os.path.join("Components", "Button.wav"))
                    self.tts_thread.play_sound(sound_path)
            except Exception:
                pass

            speak(intro)
                        
        else:
            self.leftWidget.grids[self.col][self.row].setFocus()

    ##switch to arrow mode
    def arrow_mode_switch(self, on_off):
        menu = ["MENUUP", "MENUDOWN", "MENULEFT", "MENURIGHT"]
        arrows = ["UP", "DOWN", "LEFT", "RIGHT", "SPACE", "DELETE"]
        boo = False if on_off else True
        for i in menu:
            self.arrow_shortcut.get(i).setEnabled(boo)
        for arrow in arrows:
            self.arrow_shortcut.get(arrow).setEnabled(on_off)


    ##repeat the previous sentence
    def repeat_previous(self):
        speak(previous_sentence)

    ##tell user different options based on the application status
    def helper_menu(self):
        print("helper")
        match self.main_flow_status:
            case Bot_flow_status.setting_status:
                if(self.game_play_mode == Game_play_mode.analysis_mode):
                    speak(t(Speak_template.analysis_help_message.value))
                else:
                    speak(t(Speak_template.setting_state_help_message.value))
                return
            case Bot_flow_status.board_init_status:
                speak(t(Speak_template.init_state_help_message.value))
                return
            case Bot_flow_status.select_status:
                if(Game_flow_status == Game_play_mode.computer_mode):
                    speak(t(Speak_template.select_computer_help_message.value))
                else:
                    speak(t(Speak_template.select_online_help_message.value))
            case Bot_flow_status.game_play_status:
                if self.input_mode == Input_mode.command_mode:
                    sentence = t(Speak_template.command_panel_help_message.value)
                    # if self.game_play_mode == Game_play_mode.online_mode:
                    #     sentence = (
                    #         + Speak_template.command_panel_help_message.value
                    #     )

                    speak(sentence)
                elif self.input_mode == Input_mode.arrow_mode:
                    speak(
                        t(Speak_template.arrow_mode_help_message.value)
                        + "or press control F for command mode"
                    )

    def voice_helper_menu(self):
        print("voice helper")
        match self.main_flow_status:
            case Bot_flow_status.setting_status:
                speak(t(Speak_template.setting_state_vinput_help_message.value))
                return
            case Bot_flow_status.board_init_status:
                speak(t(Speak_template.init_state_help_message.value))
                return
            case Bot_flow_status.select_status:
                if(Game_flow_status == Game_play_mode.computer_mode):
                    speak(t(Speak_template.select_computer_vinput_help_message.value))
                else:
                    speak(t(Speak_template.select_online_vinput_help_message.value))
            case Bot_flow_status.game_play_status:
                if self.input_mode == Input_mode.command_mode:
                    speak(t(Speak_template.command_panel_vinput_help_message.value))

    def setMoveList(self, move):
        print(f"MOVE = {move} Type = {type(move)}")
        if(isinstance(move, str)):
            if(self.moveList_element % 2 == 0):
                self.moveListString += str(self.moveList_line) + ". " + move.lower() + ", "
            else:
                self.moveListString += move.lower() + ", "
                self.moveList_line += 1
        else:
            if(self.moveList_element % 2 == 0):
                self.moveListString += str(self.moveList_line) + ". " + self.chessBoard.board_object.parse_san(str(move)).uci() + ", "
            else:
                self.moveListString += self.chessBoard.board_object.parse_san(str(move)).uci() + ", "
                self.moveList_line += 1
            
        if(self.moveList_element % 10 == 0 and self.moveList_element != 0):
                self.moveListString += "\n"
        self.moveList_element += 1

        self.rightWidget.moveList.setText(t("ui.move_list") + "\n" + self.moveListString)

    def refresh_move_list_from_board(self):
        """
        Update move list based on the current chessBoard.board_object.move_stack
        and update opponentBox to show the last move. Mainly used for updating after undoing a move.
        """
        if self.chessBoard is None:
            return

        # reset the counter
        self.moveListString = ""
        self.moveList_line = 1
        self.moveList_element = 0

        moves = list(self.chessBoard.board_object.move_stack)
        last_uci = None

        for idx, move in enumerate(moves):
            try:
                uci = move.uci()
            except Exception:
                # if move is not a chess.Move, try to convert it to a string
                uci = str(move)

            if self.moveList_element % 2 == 0:
                self.moveListString += f"{self.moveList_line}. {uci}, "
            else:
                self.moveListString += f"{uci}, "
                self.moveList_line += 1

            self.moveList_element += 1
            last_uci = uci

            if self.moveList_element % 10 == 0 and self.moveList_element != 0:
                self.moveListString += "\n"

        self.rightWidget.moveList.setText(t("ui.move_list") + "\n" + self.moveListString)

        # update the opponent's last move display
        if last_uci:
            self.rightWidget.opponentBox.setText(
                f"{t('ui.opponent_last_move')} {last_uci}"
            )
        else:
            self.rightWidget.opponentBox.setText(t("ui.opponent_last_move"))

    def __init__(self, *args, **kwargs):

        self.settings = QSettings('ChessBot', 'config')
        print(self.settings.fileName())

        # apply the saved language (before creating the UI)
        try:
            saved_lang = self.settings.value("language", "en")
        except Exception:
            saved_lang = "en"
        set_language(str(saved_lang))


        print(f"rate: {speak_thread.rate}")
        print(f"volume: {speak_thread.volume}")
        
        global previous_sentence
        
        self.tts_thread = speak_thread  # assign tts_thread

        self.restoreConfig()

        self._voice_trigger_mode = "toggle"

        self.alphabet = ["A", "B", "C", "D", "E", "F", "G", "H"]
        self.number = ["1", "2", "3", "4", "5", "6", "7", "8"]
        self.chess_position = [a + b for a in [x.lower() for x in self.alphabet] for b in self.number]
        self.moveListString = ""
        self.moveList_line = 1
        self.moveList_element = 0
        self.FenNotation = ""
        self.userLoginName = ""
        self.previous_game_exist = False
        self.boardDescription = []
        self._checking_exist_game = False
        self.whiteLoc = []
        self.blackLoc = []
        self.selected_bot_name = None
        self.selected_bot_category = None
        self.selected_bot_level = None
        self.timeControl = ""
        # online time control (multi-page menu) status
        self.time_control_by_category = {}
        self.time_control_by_name = {}
        self.current_timecontrol_category = None
        self.current_timecontrol_options = []
        self.selected_time_control_name = None
        self.category_combobox = None
        self.selected_bot_name = None
        self.selected_bot_category = None
        self.selected_bot_level = None
        self.bot_retry = False

        super(MainWindow, self).__init__(*args, **kwargs)

        self._audio_reminder_confirmed = False
        self._welcome_pending = False

        QTimer.singleShot(0, self._show_audio_reminder_on_startup)

        shortcut_F = QShortcut(QKeySequence("Ctrl+F"), self)
        shortcut_F.activated.connect(self.switch_command_mode)

        shortcut_J = QShortcut(QKeySequence("Ctrl+J"), self)
        shortcut_J.activated.connect(self.switch_arrow_mode)

        shortcut_S = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut_S.activated.connect(self.voice_input)
        self.voice_input_shortcut = shortcut_S

        self._apply_voice_trigger_shortcuts()

        shortcut_menu_up = QShortcut(QKeySequence(Qt.Key.Key_Up), self)
        shortcut_menu_up.activated.connect(lambda: self.handle_tab("UP"))

        shortcut_menu_down = QShortcut(QKeySequence(Qt.Key.Key_Down), self)
        shortcut_menu_down.activated.connect(lambda: self.handle_tab("DOWN"))
        
        shortcut_menu_left = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        shortcut_menu_left.activated.connect(lambda: self.handle_tab("LEFT"))

        shortcut_menu_right = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        shortcut_menu_right.activated.connect(lambda: self.handle_tab("RIGHT"))

        shortcut_arrow_UP = QShortcut(QKeySequence(Qt.Key.Key_Up), self)
        shortcut_arrow_UP.activated.connect(partial(self.handle_arrow, "UP"))

        shortcut_arrow_DOWN = QShortcut(QKeySequence(Qt.Key.Key_Down), self)
        shortcut_arrow_DOWN.activated.connect(partial(self.handle_arrow, "DOWN"))

        shortcut_arrow_LEFT = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        shortcut_arrow_LEFT.activated.connect(partial(self.handle_arrow, "LEFT"))

        shortcut_arrow_RIGHT = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        shortcut_arrow_RIGHT.activated.connect(partial(self.handle_arrow, "RIGHT"))

        shortcut_SPACE = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        shortcut_SPACE.activated.connect(self.handle_space)

        shortcut_DELETE = QShortcut(QKeySequence(Qt.Key.Key_Backspace), self)
        shortcut_DELETE.activated.connect(self.handle_arrow_delete)

        shortcut_TAB = QShortcut(QKeySequence(Qt.Key.Key_Tab), self)
        shortcut_TAB.setContext(Qt.ShortcutContext.WindowShortcut)  # valid in the entire window
        shortcut_TAB.activated.connect(lambda: self.handle_tab("TAB"))

        shortcut_F1 = QShortcut(QKeySequence("Ctrl+1"), self)
        shortcut_F1.activated.connect(self.playWithComputerHandler)

        shortcut_F2 = QShortcut(QKeySequence("Ctrl+2"), self)
        shortcut_F2.activated.connect(self.playWithOtherButtonHandler)

        shortcut_F3 = QShortcut(QKeySequence("Ctrl+3"), self)
        shortcut_F3.activated.connect(self.puzzleModeHandler)

        shortcut_R = QShortcut(QKeySequence("Ctrl+R"), self)
        shortcut_R.activated.connect(self.repeat_previous)

        shortcut_O = QShortcut(QKeySequence("Ctrl+O"), self)
        shortcut_O.activated.connect(self.helper_menu)

        shortcut_ctrlp = QShortcut(QKeySequence("Ctrl+P"), self)
        shortcut_ctrlp.activated.connect(self.voice_helper_menu)

        shortcut_H = QShortcut(QKeySequence("Ctrl+H"), self)
        shortcut_H.activated.connect(self.returnHomePage)

        shortcut_Y = QShortcut(QKeySequence("Ctrl+Y"), self)
        shortcut_Y.activated.connect(self.openSettingMenu)

        self.shortcut_current_game_analysis = QShortcut(QKeySequence("Ctrl+E"), self)
        self.shortcut_current_game_analysis.activated.connect(self.announce_game_situation)

        self.shortcut_A = QShortcut(QKeySequence("a"), self)
        self.shortcut_A.activated.connect(self.analysisModeHandler)
        
        self.arrow_shortcut = {
            "MENUUP": shortcut_menu_up,
            "MENUDOWN": shortcut_menu_down,
            "MENULEFT": shortcut_menu_left,
            "MENURIGHT": shortcut_menu_right,
            "UP": shortcut_arrow_UP,
            "DOWN": shortcut_arrow_DOWN,
            "LEFT": shortcut_arrow_LEFT,
            "RIGHT": shortcut_arrow_RIGHT,
            "SPACE": shortcut_SPACE,
            "DELETE": shortcut_DELETE,
        }

        self.arrow_mode_switch(False)

        # load the online time control configuration from time_control.txt
        self._load_time_control_from_txt()

        # analysis_Shortcut_UP = QShortcut(QKeySequence(Qt.Key.Key_Up), self)
        # analysis_Shortcut_UP.activated.connect(self.analysis_FirstMove)

        analysis_Shortcut_LEFT = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        analysis_Shortcut_LEFT.activated.connect(self.analysis_PreviousMove)

        analysis_Shortcut_RIGHT = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        analysis_Shortcut_RIGHT.activated.connect(self.analysis_NextMove)

        analysis_Shortcut_BestMove = QShortcut(QKeySequence("b"), self)
        analysis_Shortcut_BestMove.activated.connect(self.analysis_BestMove)

        analysis_Shortcut_Explanation = QShortcut(QKeySequence("e"), self)
        analysis_Shortcut_Explanation.activated.connect(self.analysis_Explanation)

        analysis_Shortcut_CurrentMove = QShortcut(QKeySequence("c"), self)
        analysis_Shortcut_CurrentMove.activated.connect(self.analysis_CurrentMove)

        self.analysis_Shortcut = {
            "B": analysis_Shortcut_BestMove,
            "E": analysis_Shortcut_Explanation,
            "C": analysis_Shortcut_CurrentMove,
            "LEFT": analysis_Shortcut_LEFT,
            "RIGHT": analysis_Shortcut_RIGHT,
        }

        self.analysis_mode_switch(False)

        shortcut_q = QShortcut(QKeySequence("Ctrl+Q"), self)
        shortcut_q.activated.connect(self.chatbot)

        ##initialize flow status
        self.main_flow_status = Bot_flow_status.setting_status
        self.game_flow_status = Game_flow_status.not_start
        self.input_mode = Input_mode.command_mode
        self.game_play_mode = None

        ##initialize UI components
        self.mainWidget = QWidget()
        self.leftWidget = LeftWidget()
        self.rightWidget = RightWidget()
        self.chatbotWidget = ChatbotWindow(
            speak_function=speak,
            tts_thread=self.tts_thread,
            voice_input_function=self.voice_input,
            voice_input_press_function=self.voice_input_press,
            voice_input_release_function=self.voice_input_release,
            fen_provider=self.get_current_fen,
        )
        # prefer to keep the focus on the chat input field (when the chatbot command is triggered)
        self._prefer_chatbot_focus = False

        def timeCallback(clocks):
            if not clocks == None:
                user_time = clocks[1].split(":")
                user = user_time[0] + " minutes " + user_time[1] + " seconds"

                opponent_time = clocks[0].split(":")
                opponent = (
                    opponent_time[0] + " minutes " + opponent_time[1] + " seconds"
                )
                speak(
                    t(
                        Speak_template.check_time_sentense.value,
                        user=user,
                        opponent=opponent,
                    )
                )

        self.rightWidget.check_time.clicked.connect(
            partial(self.leftWidget.checkTime, timeCallback)
        )
        self.rightWidget.check_being_attacked.clicked.connect(
            self.macroView
        )
        # current game analysis button: only analyze and read the current situation when the user presses it
        try:
            self.rightWidget.currentGameAnalysisButton.clicked.connect(
                self.announce_game_situation
            )
        except Exception:
            pass

        self._apply_saved_voice_trigger_mode()
        self.rightWidget.playWithComputerButton.clicked.connect(
            self.playWithComputerHandler
        )
        self.rightWidget.playWithOtherButton.clicked.connect(
            self.playWithOtherButtonHandler
        )

        self.rightWidget.puzzleModeButton.clicked.connect(
            self.puzzleModeHandler
        )

        self.rightWidget.nextPuzzleButton.clicked.connect(self.clickNextPuzzle)

        self.rightWidget.retryPuzzleButton.clicked.connect(self.retryPuzzle)

        self.rightWidget.resign.clicked.connect(self.resign_handler)

        # undo button: connect to undo_last_move
        try:
            self.rightWidget.undo_button.clicked.connect(self.undo_last_move)
        except Exception:
            pass

        self.rightWidget.loginButton.clicked.connect(lambda: self.change_main_flow_status(Bot_flow_status.login_status))
        
        self.rightWidget.logoutButton.clicked.connect(self.logout)

        self.rightWidget.chatbot_button.clicked.connect(self.chatbot)

        self.rightWidget.commandPanel.returnPressed.connect(self.CommandPanelHandler)
        self.rightWidget.check_position.returnPressed.connect(
            self.check_position_handler
        )

        self.rightWidget.loginAccount_Input.returnPressed.connect(self.loginHandler)
        self.rightWidget.loginPassword_Input.returnPressed.connect(self.loginHandler)
        self.rightWidget.login_button.pressed.connect(self.loginHandler)

        self.rightWidget.selectPanel.returnPressed.connect(self.selectPanelHandler)

        self.leftWidget.chessWebView.loadFinished.connect(self.checkLogined)

        self.leftWidget.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.getScoreTimer = QTimer()
        self.getScoreTimer.timeout.connect(self.check_score)

        self.getOpponentMoveTimer = QTimer()
        self.getOpponentMoveTimer.timeout.connect(self.getOpponentMove)

        self.check_game_end_timer = QTimer()
        self.check_game_end_timer.timeout.connect(self.check_game_end)

        self.cooldownTimer = QTimer()
        self.cooldownTimer.timeout.connect(self.reset_cooldown)
        self.cooldown = False

        mainLayout = QHBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)
        
        # Redesign layout: 3/5 chess.com, 1/3 button interface, 1/3 chatbot
        mainLayout.addWidget(self.leftWidget, 9)  # chess.com takes 3/5
        mainLayout.addWidget(self.rightWidget, 5)  # button interface takes 1/3
        mainLayout.addWidget(self.chatbotWidget, 5)  # chatbot takes 1/3

        # ensure the middle button interface is visible, avoid being compressed to width 0
        self.rightWidget.setMinimumWidth(320)
        self.rightWidget.setVisible(True)

        self.mainWidget.setLayout(mainLayout)
        self.setCentralWidget(self.mainWidget)

        # ensure the chatbot widget is visible
        self.chatbotWidget.setVisible(True)
        self.chatbotWidget.show()
        self.chatbotWidget.setMinimumSize(300, 400)

        # allow the main window to be dragged and adjusted by the user, and give the initial size according to the screen ratio
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            screen_w = available.width()
            screen_h = available.height()
        else:
            screen_w, screen_h = 1920, 1080

        init_w = int(screen_w * 0.90)
        init_h = int(screen_h * 0.85)
        min_w = int(screen_w * 0.60)
        min_h = int(screen_h * 0.55)

        # minimum size, avoid being too small on a small screen
        init_w = max(init_w, 1280)
        init_h = max(init_h, 720)
        min_w = max(min_w, 1000)
        min_h = max(min_h, 600)

        self.setMinimumSize(min_w, min_h)
        self.resize(init_w, init_h)
        self.setMaximumSize(16777215, 16777215)

        # force update the layout
        mainLayout.update()
        mainLayout.activate()

        self.chessBoard = None
        self.userColor = None
        self.opponentColor = None
        self.online_game_started = False
        self._last_opponent_row_sig = ""
        ##need to modify /Users/longlong/miniforge3/envs/fyp/lib/python3.12/site-packages/pyttsx3/drivers/nsss.py
        ## import objc and self.super
        # self.rightWidget.playWithComputerButton.setFocus()
        self.currentFocus = 0

        self.rightWidget.settingButton.clicked.connect(self.openSettingMenu)

        # Play with online player - multi-page time control menu
        # first page: category buttons (Bullet / Blitz / Rapid / Daily)
        for category, btn in self.rightWidget.online_category_buttons.items():
            btn.clicked.connect(lambda checked=False, c=category: self.open_online_selection_page(c))

        # second page: specific time control selection buttons (dynamic update text based on different categories)
        for index, btn in enumerate(self.rightWidget.online_selection_buttons):
            btn.clicked.connect(lambda checked=False, idx=index: self.handle_online_selection_button(idx))

        # return to the previous page (from the selection page to the category page)
        self.rightWidget.back_to_previous_page_button.clicked.connect(self.open_online_category_page)

        # second page: start game button at the bottom
        self.rightWidget.online_start_game_button.clicked.connect(self.start_online_game)

## bot category
        self.rightWidget.playWithComputerButton_Coach.clicked.connect(lambda: self.bot_select_category("coach"))
        self.rightWidget.playWithComputerButton_Adaptive.clicked.connect(lambda: self.bot_select_category("adaptive"))
        self.rightWidget.playWithComputerButton_Beginner.clicked.connect(lambda: self.bot_select_category("beginner"))
        self.rightWidget.playWithComputerButton_Intermediate.clicked.connect(lambda: self.bot_select_category("intermediate"))
        self.rightWidget.playWithComputerButton_Advanced.clicked.connect(lambda: self.bot_select_category("advanced"))
        self.rightWidget.playWithComputerButton_Master.clicked.connect(lambda: self.bot_select_category("master"))
        self.rightWidget.playWithComputerButton_Athletes.clicked.connect(lambda: self.bot_select_category("athletes"))
        self.rightWidget.playWithComputerButton_Musicians.clicked.connect(lambda: self.bot_select_category("musicians"))
        self.rightWidget.playWithComputerButton_Creators.clicked.connect(lambda: self.bot_select_category("creators"))
        self.rightWidget.playWithComputerButton_TopPlayers.clicked.connect(lambda: self.bot_select_category("top_players"))
        self.rightWidget.playWithComputerButton_Personalities.clicked.connect(lambda: self.bot_select_category("personalities"))
        self.rightWidget.playWithComputerButton_Engine.clicked.connect(lambda: self.bot_select_category("engine"))
        self.rightWidget.back_to_category_button.clicked.connect(self.back_to_category)

        # bot list buttons (per category)
        for category_key, buttons in self.rightWidget.bot_category_buttons.items():
            for btn in buttons:
                btn.clicked.connect(lambda checked=False, b=btn: self.select_bot_from_button(b))

## analysis mode button connection
        self.rightWidget.gamereviewButton.clicked.connect(self.analysisModeHandler)
        self.rightWidget.analysis_NextMove_Button.clicked.connect(self.analysis_NextMove)
        self.rightWidget.analysis_PreviousMove_Button.clicked.connect(self.analysis_PreviousMove)
        self.rightWidget.analysis_FirstMove_Button.clicked.connect(self.analysis_FirstMove)
        self.rightWidget.analysis_BestMove_Button.clicked.connect(self.analysis_BestMove)
        # self.rightWidget.analysis_Explanation_Button.clicked.connect(self.analysis_Explanation)
        # self.rightWidget.analysis_CurrentMove_Button.clicked.connect(self.analysis_CurrentMove)
        # self.rightWidget.analysis_LastMove_Button.clicked.connect(self.analysis_LastMove)

        self.rightWidget.newgameButton.clicked.connect(self.newGame)
        self.rightWidget.returnToHomePageButton.clicked.connect(self.returnHomePage)

        voice_input_thread.action_signal.connect(self.check_action) #receive voice input signal
        voice_input_thread.transcribed_signal.connect(self.handle_transcribed_text)
        self.chatbotWidget.action_signal.connect(self.handle_chatbot_action) 

        

    def apply_font_size(self, font_size: int):
        try:
            size = int(font_size)
        except (TypeError, ValueError):
            size = 22
        size = max(10, min(40, size))
        app = QApplication.instance()
        if app is None:
            return
        font = app.font()
        font.setPointSize(size)
        app.setFont(font)
        self._current_font_size = size

## restore user settings
    def restoreConfig(self):
        global internal_speak_engine
        speak_thread.setRateValue(int(self.settings.value('rate', 200)))    # Restore User Config
        speak_thread.setVolumeValue(float(self.settings.value('volume', 0.7)))
        internal_speak_engine = bool(self.settings.value('speak_engine', True))
        saved_font_size = self.settings.value('font_size', 22)
        self.apply_font_size(saved_font_size)
        try:
            saved_lang = self.settings.value('language', 'en')
            speak_thread.update_language(saved_lang)
        except Exception:
            pass

## store user settings
    def closeEvent(self, event):
        global internal_speak_engine
        self.settings.setValue('rate', str(speak_thread.getRateValue()))
        self.settings.setValue('volume', str(speak_thread.getVolumeValue()))
        self.settings.setValue('speak_engine', '1' if internal_speak_engine else '')
        self.settings.setValue('font_size', str(getattr(self, "_current_font_size", 22)))

## handle start a new game
    def newGame(self):
        timeControl = self.timeControl
        game_play_mode = self.game_play_mode
        print(f"time control = {timeControl}")
        self.change_main_flow_status(Bot_flow_status.setting_status)
        match(game_play_mode):
            case Game_play_mode.computer_mode:
                print("Restart Computer Game")
                speak(t("speak.game.restart_computer_game"))

                def start_computer_new_game(result):
                    # if the current page cannot find Rematch/New Game, return to the computer game page and restart
                    if not result:
                        self.playWithComputerHandler()

                    self.change_main_flow_status(Bot_flow_status.board_init_status)
                    QTimer.singleShot(800, self.getColor)
                    QTimer.singleShot(1000, self.initBoard)
                    QTimer.singleShot(1200, self.getBoard)
                    QTimer.singleShot(1400, lambda: self.change_main_flow_status(Bot_flow_status.game_play_status))

                self.runJavaScriptSafe(js_function.bot_new_game, start_computer_new_game)

            case Game_play_mode.online_mode:
                print("Starting a new game")
                speak(t("speak.game.starting_new_game"))

                # after resigning, usually still on the game result page, return to the online setup page and start a new game
                def on_online_loaded(_ok):
                    try:
                        self.leftWidget.chessWebView.loadFinished.disconnect(on_online_loaded)
                    except Exception:
                        pass
                    QTimer.singleShot(1200, lambda: self.check_action(timeControl))

                try:
                    self.leftWidget.chessWebView.loadFinished.connect(on_online_loaded)
                    self.leftWidget.chessWebView.load(QUrl("https://www.chess.com/play/online"))
                except Exception:
                    self.check_action(timeControl)

## back to main phase (game mode selection)
    def returnHomePage(self):
        self.online_game_started = False
        self.getOpponentMoveTimer.stop()
        if(self.game_play_mode == Game_play_mode.analysis_mode):
            self.keyPressed_Signal.disconnect(self.analysisAction)
            self.shortcut_A.activated.connect(self.analysisModeHandler)
            self.analysis_mode_switch(False)
        self.leftWidget.chessWebView.load(QUrl("https://www.chess.com"))
        self.change_main_flow_status(Bot_flow_status.setting_status)
        speak(t("speak.game.returned_home"))

## function to announce the pieces being attacked
    def macroView(self):
        # prevent crash: do not execute if the board is not initialized
        if self.chessBoard is None or self.chessBoard.board_object is None:
            speak(t("speak.game.no_active_macro_unavailable"))
            return
        if self.userColor is None:
            speak(t("speak.game.color_not_assigned"))
            return
        self.exist_square = []
        black = ["q", "n", "r", "b","p","k"]
        white = ["Q", "N", "R", "B","P","K"]
        attacked_messages = []
        match(self.userColor):
            case "WHITE":
                for square in chess.SQUARES:
                    piece = self.chessBoard.board_object.piece_at(square)
                    if piece is not None and str(piece) in white:
                        self.exist_square.append(square)
                for i in self.exist_square:
                    piece = self.chessBoard.board_object.piece_at(i)
                    if self.chessBoard.board_object.is_attacked_by(chess.BLACK, i):
                        msg = f"Piece {PIECES_SHORTFORM_CONVERTER[piece.symbol()]} at square {chess.SQUARE_NAMES[i]} is being attacked"
                        print(msg)
                        attacked_messages.append(msg)
            case "BLACK":
                for square in chess.SQUARES:
                    piece = self.chessBoard.board_object.piece_at(square)
                    if piece is not None and str(piece) in black:
                        self.exist_square.append(square)
                for i in self.exist_square:
                    piece = self.chessBoard.board_object.piece_at(i)
                    if self.chessBoard.board_object.is_attacked_by(chess.WHITE, i):
                        msg = f"Piece {PIECES_SHORTFORM_CONVERTER[piece.symbol()]} at square {chess.SQUARE_NAMES[i]} is being attacked"
                        print(msg)
                        attacked_messages.append(msg)
        try:
            # prepare the chatbox text
            if len(attacked_messages) == 0:
                chat_text = t("chat.macro.none_under_attack")
                speak(t("speak.game.no_pieces_under_attack"))
            else:
                max_items = 12
                shown = attacked_messages[:max_items]
                remainder = len(attacked_messages) - len(shown)
                chat_lines = [t("chat.macro.under_attack_count", count=len(attacked_messages))] + shown
                if remainder > 0:
                    chat_lines.append(f"And {remainder} more.")
                chat_text = "\n".join(chat_lines)

                # voice: first summarize, then read each one
                speak(t("speak.game.macro_under_attack_count", count=len(attacked_messages)))
                for line in shown:
                    speak(line)
                if remainder > 0:
                    speak(t("speak.game.and_more_count", count=remainder))

            # write to the chatbox
            try:
                if hasattr(self, 'chatbotWidget') and hasattr(self.chatbotWidget, 'chat_display'):
                    self.chatbotWidget.chat_display.append(f"Chatbot: {chat_text}")
            except Exception as e2:
                print("Append macro view to chat failed:", e2)
        except Exception as e:
            print("Speak macro view failed:", e)

    def get_current_fen(self, field: str = "fen"):
        """
        Provide current board info for chatbot queries.
        field: "fen", "fen_latest", "fen_sync_request", or "user_color"
        """
        if field == "user_color":
            if getattr(self, "userColor", None):
                return "white" if self.userColor == "WHITE" else "black"
            return None

        if field == "fen_sync_request":
            # no-share mode: do not trigger the webpage Share fetch, directly use the internal board
            return None

        if field == "fen_latest":
            # no-share mode: do not use the webpage cache FEN, avoid returning old values
            if not getattr(self, "enable_share_fen_sync", False):
                return None
            latest_fen = getattr(self, "_latest_web_fen", None)
            latest_time = getattr(self, "_latest_web_fen_time", None)
            try:
                if latest_fen and latest_time and (time.time() - latest_time) <= 10.0:
                    return latest_fen
            except Exception:
                pass
            return None

        board_wrapper = getattr(self, "chessBoard", None)
        # if the current game is not in progress (e.g. resigned or game ended), do not provide FEN
        try:
            if getattr(self, "game_flow_status", None) == Game_flow_status.game_end:
                return None
        except Exception:
            pass
        if not board_wrapper:
            return None
        board_object = getattr(board_wrapper, "board_object", None)
        if board_object is None:
            return None

        try:
            # only allow using the webpage cache FEN when share sync is enabled
            if getattr(self, "enable_share_fen_sync", False):
                latest_fen = getattr(self, "_latest_web_fen", None)
                latest_time = getattr(self, "_latest_web_fen_time", None)
                # if the webpage has synced to FEN recently, use it first (avoid falling behind the opponent's move)
                if latest_fen and latest_time and (time.time() - latest_time) <= 5.0:
                    return latest_fen
            # no-share mode: directly return the internal board FEN
            return board_object.fen()
        except Exception as exc:
            print(f"Unable to get current FEN: {exc}")
            return None
    
    def announce_game_situation(self):
        """
        when detecting an unfinished game, automatically analyze the current situation and announce it to the user
        """
        # get the current FEN
        fen_value = self.get_current_fen()
        if not fen_value:
            print("unable to get the current FEN, skip the game situation analysis")
            return
        
        # get the user color information (if not set, infer from the current turn)
        if hasattr(self, 'userColor') and self.userColor:
            user_color_text = "white" if self.userColor == "WHITE" else "black"
        else:
            # if userColor is not set, infer from the current turn
            user_color_text = "unknown"
        
        # get the current turn information
        if hasattr(self, 'game_flow_status'):
            turn_text = "your turn" if self.game_flow_status == Game_flow_status.user_turn else "opponent's turn"
        else:
            turn_text = "unknown turn"
        
        analysis_prompt = (
            "code:8888 "
        )
        
        print("Analyzing current game situation")
        speak(t("speak.analysis.analyzing_current_game"))
        
        
        if hasattr(self, 'chatbotWidget') and self.chatbotWidget:
            
            from ui.chatbot_window import replicateWorker
            
            def on_analysis_complete(full_payload: dict):
               
                reply_text = str(full_payload.get("reply") or "").strip()
                print(f"Chess game analysis completed: {reply_text}")
                chatbot_response = reply_text
                if not chatbot_response:
                    return
                try:
                   
                    if hasattr(self, "chatbotWidget") and self.chatbotWidget:
                        self.chatbotWidget.add_system_bot_message(chatbot_response)
                    else:
                        speak(chatbot_response)
                except Exception:
                    
                    speak(chatbot_response)
            
            def on_analysis_token(token: str):
                
                pass
            
        
            history_payload = []
            session_id = None
            try:
                history_payload = list(getattr(self.chatbotWidget, "chat_history", []) or [])
                session_id = getattr(self.chatbotWidget, "session_id", None)
            except Exception:
                history_payload = []
                session_id = None

            self._game_situation_worker = replicateWorker(
                message=analysis_prompt,
                fen=fen_value,
                user_color=user_color_text if user_color_text in {"white", "black"} else None,
                history=history_payload,
                session_id=session_id,
            )
            self._game_situation_worker.token_signal.connect(on_analysis_token)
            self._game_situation_worker.done_signal.connect(on_analysis_complete)
            self._game_situation_worker.start()
        else:
            print("Chatbot widget not initialized, unable to perform AI analysis")
            speak(t("speak.analysis.unable_to_analyze"))

## display chatbot interface
    def chatbot(self):
           
            self.chatbotWidget.setVisible(True)
            self.chatbotWidget.show()
            
            if hasattr(self.chatbotWidget, 'message_input'):
                self.chatbotWidget.message_input.setFocus()
                self.chatbotWidget.message_input.activateWindow()
                
                QTimer.singleShot(100, lambda: self.chatbotWidget.message_input.setFocus())
            # speak("Hello! I am a Chat Bot. How can I help you today? Type in your question and I will answer immediately. You can type in how to use for help.")
    
    def handle_transcribed_text(self, text: str):
        
        if not text:
            return
        try:
            speak(t("speak.chat.user_input", message=text))
        except Exception:
            pass
        
        voice_input_thread.processed_by_chatbot = True
        
        self.chatbotWidget.add_user_bubble(text)
        
        result = self.chatbotWidget.get_bot_response(text.lower())

        delegated_message = None
        if isinstance(result, tuple):
            response, delegated_message = result
        else:
            response = result

        if response:
            
            self.chatbotWidget.add_system_bot_message(response)
            
            return

        
        self.chatbotWidget.start_replicate_for(delegated_message or text)

    # make action based on chatbot command (text input)
    def handle_chatbot_action(self, action: str):
        print(f"Received chatbot action: {action}")
        if not action:
            return
        raw_action = action.strip()
        normalized = raw_action.lower()

        # Direct chess operations from chatbot
        if normalized.startswith("move:"):
            move = raw_action.split(":", 1)[1].strip()
            if not move:
                return
            if (
                self.chessBoard is None
                or getattr(self.chessBoard, "board_object", None) is None
            ):
                warning_msg = "No active game board detected. Please start or load a game before making moves."
                print(warning_msg)
                try:
                    if hasattr(self, "chatbotWidget") and hasattr(
                        self.chatbotWidget, "chat_display"
                    ):
                        self.chatbotWidget.chat_display.append(f"Chatbot: {warning_msg}")
                except Exception:
                    pass
                speak(warning_msg)
                return
            self._execute_user_move(move, source="chatbot")
            
            self._prefer_chatbot_focus = True
            self.focus_chatbot_input()
            QTimer.singleShot(700, self.focus_chatbot_input)
            QTimer.singleShot(1500, lambda: setattr(self, "_prefer_chatbot_focus", False))
            return

        if normalized.startswith("check:"):
            query = normalized.split(":", 1)[1].strip()
            if not query:
                return
            
            try:
                self.rightWidget.check_position.setText(query)
                self.check_position_handler()
            finally:
                self.rightWidget.check_position.clear()
            return

        # Handle structured timecontrol
        if normalized.startswith("vc:"):
            parts = normalized.split(":")
            if len(parts) >= 3 and parts[1] == "timecontrol":
                timeControl = parts[2]
                self.check_action(timeControl)
            return

        # Explicit routing to avoid accidental new game
        if normalized == "login":
            self.change_main_flow_status(Bot_flow_status.login_status)
            return
        if normalized == "logout":
            self.logout()
            return
        if normalized == "start_computer_game":
            self.playWithComputerHandler()
            return
        if normalized in {"start_player_game", "start_online_game"}:
            self.playWithOtherButtonHandler()
            return
        if normalized == "get_board_state":
            self.getBoard()
            return
        if normalized in {"home", "return_home"}:
            self.returnHomePage()
            return
        if normalized in {"puzzle", "start_puzzle"}:
            self.puzzleModeHandler()
            return

        # Resign current game
        if normalized == "resign":
            self.resign_handler()
            return

        if normalized == "open_settings":
            self.openSettingMenu()
            return

        if normalized == "undo_last_move":
            self.undo_last_move()
            return

        # Macro View (piece attack overview)
        if normalized == "macro_view":
            try:
                if self.chessBoard is None:
                    speak(t("speak.game.no_active_start_or_resume"))
                    return
                print("Invoking macro view via chatbot...")
                QTimer.singleShot(200, self.macroView)
            except Exception as e:
                try:
                    speak(t("speak.game.macro_view_failed"))
                except:
                    pass
                print("Macro view error:", e)
            return

        # Allow explicit timecontrol-like text
        known_prefixes = ["1+", "3+", "5+", "10+", "15+", "30+", "bullet", "blitz", "rapid"]
        if any(normalized.startswith(p) for p in known_prefixes) or normalized.isdigit():
            self.check_action(normalized)
        else:
            print("Ignored unrecognized chatbot command:", action)

    def focus_chatbot_input(self):
        try:
            if hasattr(self, 'chatbotWidget') and hasattr(self.chatbotWidget, 'message_input'):
                
                self.chatbotWidget.message_input.setFocus()
                self.chatbotWidget.message_input.activateWindow()
               
                for delay in [50, 150, 300, 600]:
                    QTimer.singleShot(delay, lambda: self.chatbotWidget.message_input.setFocus())
        except:
            pass
    
## handle setting menu
    def openSettingMenu(self):
        global internal_speak_engine
        
        try:
            current_lang = self.settings.value("language", "en")
        except Exception:
            current_lang = "en"
        previous_lang = str(current_lang)

        speak(t("speak.settings.opened_hint"))

        def _apply_temp_language(lang_value: str):
            try:
                set_language(lang_value)
                if hasattr(self, 'rightWidget') and self.rightWidget:
                    self.rightWidget.retranslate_ui()
                if hasattr(self, 'chatbotWidget') and self.chatbotWidget:
                    self.chatbotWidget.retranslate_ui()
            except Exception:
                pass

        menu = SettingMenu(
            rate=int((speak_thread.getRateValue() - 100) * 0.5),
            volume=int(speak_thread.getVolumeValue() * 100),
            engine=internal_speak_engine,
            language=str(current_lang),
            font_size=getattr(self, "_current_font_size", 22),
            speak_func=speak,
            language_change_callback=_apply_temp_language,
        )
        try:
            menu.set_voice_trigger_mode(self.settings.value("voice_trigger_mode", "toggle"))
        except Exception:
            menu.set_voice_trigger_mode("toggle")
        print(f"rate: {speak_thread.getRateValue()}, volume: {speak_thread.getVolumeValue()}")
        # menu.speech_rate_slider.setValue()
        # menu.speech_volume_slider.setValue()

        if menu.exec():
            self.speech_rate = menu.get_rate_value() * 2 + 100  # change to scale of interval 100 to 300
            self.speech_volume = menu.get_volume_value()
            internal_speak_engine = menu.get_engine_value()
            speak_thread.setRateValue(self.speech_rate)
            speak_thread.setVolumeValue(self.speech_volume)

           
            selected_lang = menu.get_language_value()
            try:
                self.settings.setValue("language", selected_lang)
            except Exception:
                pass
            set_language(selected_lang)
            try:
                self.rightWidget.retranslate_ui()
                if hasattr(self, 'chatbotWidget') and self.chatbotWidget:
                    self.chatbotWidget.retranslate_ui()
            except Exception:
                pass

            
            try:
                if hasattr(self, "moveListString"):
                    self.rightWidget.moveList.setText(t("ui.move_list") + "\n" + str(self.moveListString))

                # Assigned Color
                user_color = getattr(self, "userColor", None)
                if user_color:
                    self.rightWidget.colorBox.setText(f"{t('ui.assigned_color')} {user_color}")
                else:
                    self.rightWidget.colorBox.setText(t("ui.assigned_color"))

                # Opponent Last Move
                try:
                    current_opponent_text = self.rightWidget.opponentBox.text() or ""
                    raw = current_opponent_text.strip()
                    if raw:
                        marker = ":"
                        if marker in raw:
                            last_part = raw.split(marker, 1)[1].strip()
                        else:
                            
                            parts = raw.split()
                            last_part = parts[-1] if parts else ""
                        if last_part:
                            self.rightWidget.opponentBox.setText(f"{t('ui.opponent_last_move')} {last_part}")
                        else:
                            self.rightWidget.opponentBox.setText(t("ui.opponent_last_move"))
                    else:
                        self.rightWidget.opponentBox.setText(t("ui.opponent_last_move"))
                except Exception:
                    self.rightWidget.opponentBox.setText(t("ui.opponent_last_move"))

                self.runJavaScriptSafe(
                    js_function.getPiecesLocation,
                    self.getPiecesLocation,
                )
            except Exception:
                pass
            
            try:
                speak_thread.update_language(selected_lang)
            except Exception:
                pass

            
            selected_font_size = menu.get_font_size_value()
            self.apply_font_size(selected_font_size)
            try:
                self.settings.setValue("font_size", selected_font_size)
            except Exception:
                pass

            
            try:
                self.settings.setValue("voice_trigger_mode", menu.get_voice_trigger_mode())
            except Exception:
                pass
            self._voice_trigger_mode = menu.get_voice_trigger_mode()
            self._apply_voice_trigger_shortcuts()
        else:
            
            try:
                set_language(previous_lang)
                self.rightWidget.retranslate_ui()
                if hasattr(self, 'chatbotWidget') and self.chatbotWidget:
                    self.chatbotWidget.retranslate_ui()
            except Exception:
                pass

    def undo_last_move(self):
        
        global speak
        if self.chessBoard is None or self.game_play_mode is None:
            speak(t("speak.game.undo.no_move"))
            return
        try:
            stack_len = len(self.chessBoard.board_object.move_stack)
            if stack_len == 0:
                speak(t("speak.game.undo.no_move"))
                return
            
            pop_count = 1 if stack_len == 1 else 2
            for _ in range(pop_count):
                last_move = self.chessBoard.board_object.pop()
                print(f"Undo move: {last_move}")

            
            try:
                jsCode = """
                (function() {
                    try {
                        const btn = document.querySelector("#board-layout-sidebar > div > div.play-controller-component.sidebar-controller-component > div:nth-child(4) > div > div.primary-controls-topControls > button:nth-child(2)");
                        if (btn) {
                            btn.click();
                            console.error("clicked undo last move button");
                            return "clicked";
                        }
                        console.error("undo last move button not found");
                        return "not_found";
                    } catch (e) {
                        console.error("undo last move js error", e);
                        return "error";
                    }
                })();
                """
                self.runJavaScriptSafe(jsCode)
            except Exception as e_js:
                print(f"undo_last_move JS failed: {e_js}")

           
            try:
                self.refresh_move_list_from_board()
            except Exception as e_refresh:
                print(f"refresh_move_list_from_board failed: {e_refresh}")

         
            try:
                turn_color = "WHITE" if self.chessBoard.board_object.turn else "BLACK"
                if turn_color == self.userColor:
                    self.game_flow_status = Game_flow_status.user_turn
                    self.getOpponentMoveTimer.stop()
                else:
                    self.game_flow_status = Game_flow_status.opponent_turn
                    self.getOpponentMoveTimer.start(1000)
            except Exception as e_turn:
                print(f"undo turn sync failed: {e_turn}")

        
            try:
                QTimer.singleShot(
                    500,
                    lambda: self.runJavaScriptSafe(
                        js_function.getPiecesLocation, self.getPiecesLocation
                    ),
                )
            except Exception as e_pieces:
                print(f"refresh pieces after undo failed: {e_pieces}")

            speak(t("speak.game.undo.done"))
        except Exception as e:
            print(f"Undo failed: {e}")
            speak(t("speak.game.undo.no_move"))

## Game Review Function
    def analysisModeHandler(self):
        def setMoveLength(length):
            self.moveLength = length
            print(f"moveLength = {self.moveLength}")

        def callback0(x):
            QTimer.singleShot(500, lambda: self.runJavaScriptSafe(js_function.getGameId, callback1))

        def callback1(gameId):
            print(gameId)
            self.leftWidget.chessWebView.loadFinished.connect(lambda: QTimer.singleShot(3000, lambda: self.runJavaScriptSafe(js_function.checkReviewLimited, callback2)))
            if(self.game_play_mode == Game_play_mode.computer_mode):
                self.leftWidget.chessWebView.load(QUrl(f"https://www.chess.com/analysis/game/computer/{gameId}"))
            else:
                self.leftWidget.chessWebView.load(QUrl(f"https://www.chess.com/analysis/game/live/{gameId}"))

        def callback2(ReviewLimited):
            print(f"Reivew Limited: {ReviewLimited}")
            self.leftWidget.chessWebView.loadFinished.disconnect()
            if(ReviewLimited):
                print("You have used your free Game Review for the day.")
                speak(t("speak.analysis.free_review_used"))
                self.shortcut_A.activated.connect(self.analysisModeHandler)
            else:
                # self.leftWidget.key_signal.connect(self.analysisAction)
                self.analysis_mode_switch(True)
                self.keyPressed_Signal.connect(self.analysisAction)
                self.runJavaScriptSafe(js_function.clickStartReview, callback3)
                self.change_game_mode(Game_play_mode.analysis_mode)

        def callback3(value):
            if(value == None):
                QTimer.singleShot(1000, lambda: self.runJavaScriptSafe(js_function.clickStartReview, callback3))
            else:
                callback4(value)

        def callback4(comment):
            QTimer.singleShot(300, lambda: self.runJavaScriptSafe(js_function.analysis_GetMoveLength, setMoveLength))
            self.leftWidget.chessWebView.setFocus()
            self.gameReviewMode_Reader(comment)

        def checkLogin(button):
            if(button != None):
                print("Please login for Game Review Function")
                speak(t("speak.analysis.login_required"))
                return
            self.shortcut_A.activated.disconnect()
            self.bestExist = False
            self.analysisCount = 0
            self.keyPressed = None
            self.analysisBoard = ChessBoard()
            self.moveLength = -1
            self.best_pressed = False
            self.runJavaScriptSafe(js_function.clickGameReview, callback0)
        
        # if(self.game_flow_status != Game_flow_status.game_end):
        #     print("No finished game for analysis")
        #     speak("No finished game for analysis")
        #     return
        self.runJavaScriptSafe(js_function.checkLogin, checkLogin)
        


    def gameReviewMode_Reader(self, comment):
        print(comment)
        if(isinstance(comment, list)):
            self.feedback = comment[0]
            self.explain = comment[1]
            self.bestExist = comment[2]
            print(f"Signal: {self.keyPressed_Signal}, Left: {Qt.Key.Key_Left}")
            print(f"analysis Count: {self.analysisCount}")
            if(self.keyPressed == Qt.Key.Key_Left):
                if(self.analysisCount==0):
                    self.analysisBoard.board_object.pop()
                else:
                    self.analysisBoard.board_object.pop()
                    self.analysisBoard.board_object.pop()

            print(f"Board: {self.analysisBoard.board_object}")
            sanString = self.feedback.split(" ")[0].strip()
            print(f"sanstring: {sanString}")
            # self.rightWidget.analysisCurrentMove.setText("Current Move: \n" + sanString + ", ")
            print(f"feedback: {self.feedback}")
            self.feedback = self.feedback.replace(sanString, self.analysisHumanForm(self.feedback))
            if(self.best_pressed):
                self.runJavaScriptSafe(js_function.analysis_retry)
                self.analysisBoard.board_object.pop()
                self.best_pressed = False
            if(self.explain != None):
                self.rightWidget.analysisExplanation.setText(t("ui.analysis.explanation") + "\n" + self.explain)
            else:
                self.rightWidget.analysisExplanation.setText(t("ui.analysis.explanation") + " No content")
        else:
            if(self.keyPressed == Qt.Key.Key_Left):
                self.analysisBoard.board_object.pop()
            self.feedback = comment
            self.rightWidget.analysisCurrentMove.setText(t("ui.analysis.current_move") + t("speak.analysis.this_is_beginning"))

        print(self.analysisBoard.board_object)
        self.rightWidget.analysisComment.setText(t("ui.analysis.comment") + "\n" + self.feedback)
        print(self.feedback)
        speak(self.feedback)

    def gameReviewMode_Explainer(self):
        print(self.explain)
        speak(self.explain)

    def getReviewComment(self):
        self.runJavaScriptSafe(js_function.getReviewComment, self.gameReviewMode_Reader)

    def analysisAction(self, key):
        if(self.game_play_mode == Game_play_mode.analysis_mode):
            print(f"key: {key}")
            match key:
                case Qt.Key.Key_Left:
                    self.keyPressed = Qt.Key.Key_Left
                    if(self.analysisCount == 0):
                        speak(t("speak.analysis.this_is_beginning"))
                    else:
                        self.analysisCount -= 1
                        QTimer.singleShot(300, self.getReviewComment)
                        
                case Qt.Key.Key_Right:
                    self.keyPressed = Qt.Key.Key_Right
                    if(self.analysisCount == self.moveLength):
                        speak(t("speak.analysis.this_is_last_move"))
                    else:
                        self.analysisCount += 1
                        QTimer.singleShot(300, self.getReviewComment)

                case Qt.Key.Key_Up:
                    self.keyPressed = Qt.Key.Key_Up
                    self.analysisCount = 0
                    self.analysisBoard = ChessBoard()
                    print(self.analysisBoard)
                    QTimer.singleShot(300, self.getReviewComment)

                # case Qt.Key.Key_Down:
                #     QTimer.singleShot(300, self.getReviewComment)

                case Qt.Key.Key_E:
                    self.keyPressed = Qt.Key.Key_E
                    self.gameReviewMode_Explainer()

                case Qt.Key.Key_B:
                    if(self.bestExist):
                        self.keyPressed = Qt.Key.Key_B
                        self.best_pressed = True
                        self.runJavaScriptSafe(js_function.analysis_GetBestMove)
                        self.poppedMove = self.analysisBoard.board_object.pop()
                        QTimer.singleShot(1000, self.getReviewComment)
                    else:
                        print("The current move is the best move")
                        speak(t("speak.analysis.current_is_best"))

                case Qt.Key.Key_C:
                    speak(self.rightWidget.analysisCurrentMove.text())

    def analysisHumanForm(self, move):
        sanString = move.split(" ")[0].strip()
        uciString = str(self.analysisBoard.board_object.parse_san(sanString))
        en_passant = self.analysisBoard.board_object.has_legal_en_passant()
        srcLocation = uciString[:2]
        destLocation = uciString[2:4]

        src = self.analysisBoard.parseSquare(srcLocation)
        dest = self.analysisBoard.parseSquare(destLocation)
        result = ""

        src_piece_type = self.analysisBoard.board_object.piece_at(src)
        dest_piece_type = self.analysisBoard.board_object.piece_at(dest)
        srcPiece = PIECES_SHORTFORM_CONVERTER[str(src_piece_type)]
        if(dest_piece_type is not None):
            destPiece = PIECES_SHORTFORM_CONVERTER[str(dest_piece_type)]
        
        if sanString.count("x"):
            if(en_passant and str(src_piece_type).lower() == "p" and dest_piece_type is None):
                result = (f"{srcPiece} on {srcLocation} capture pawn on {uciString[2]+uciString[1]} by en passant")
            else:
                result = (f"{srcPiece} on {srcLocation} captures {destPiece} on {destLocation}")
        elif sanString.count("O-O-O"):
            result = "Queenside castling"
        elif sanString.count("O-O"):
            result = "Kingside castling"
        else:
            result = (f"{srcPiece} on {srcLocation} moves to {destLocation}")
        
        if(sanString.count("=")):
            result += f" then promoted to {PIECES_SHORTFORM_CONVERTER[uciString[4]]}"

        if(self.keyPressed == Qt.Key.Key_B):
            self.analysisBoard.board_object.push(self.poppedMove)
            self.keyPressed = None
            self.best_pressed = True
            print(self.analysisBoard)
        else:
            self.analysisBoard.board_object.push_san(sanString)

        self.rightWidget.analysisCurrentMove.setText((t("ui.analysis.current_move") + "\n" + result))
        return result
    
    def analysis_NextMove(self):
        if (self.cooldown == True):
            return
        self.cooldown = True
        self.cooldownTimer.start(500)
        self.runJavaScriptSafe(js_function.analysis_NextMove)
        QTimer.singleShot(100, lambda: self.keyPressed_Signal.emit(Qt.Key.Key_Right))

    def analysis_PreviousMove(self):
        if (self.cooldown == True):
            return
        self.cooldown = True
        self.cooldownTimer.start(500)
        self.runJavaScriptSafe(js_function.analysis_PreviousMove)
        QTimer.singleShot(100, lambda: self.keyPressed_Signal.emit(Qt.Key.Key_Left))

    def analysis_FirstMove(self):
        if (self.cooldown == True):
            return
        self.cooldown = True
        self.cooldownTimer.start(500)
        self.runJavaScriptSafe(js_function.analysis_FirstMove)
        QTimer.singleShot(100, lambda: self.keyPressed_Signal.emit(Qt.Key.Key_Up))

    # def analysis_LastMove(self):
    #     self.runJavaScriptSafe(js_function.analysis_LastMove)
    #     QTimer.singleShot(300, lambda: self.keyPressed_Signal.emit(Qt.Key.Key_Down))

    def analysis_BestMove(self):
        if (self.cooldown == True):
            return
        self.cooldown = True
        self.cooldownTimer.start(500)
        QTimer.singleShot(100, lambda: self.keyPressed_Signal.emit(Qt.Key.Key_B))

    def analysis_Explanation(self):
        self.keyPressed_Signal.emit(Qt.Key.Key_E)

    def analysis_CurrentMove(self):
        self.keyPressed_Signal.emit(Qt.Key.Key_C)

    def reset_cooldown(self):
        self.cooldown = False
        self.cooldownTimer.stop()

    def analysis_mode_switch(self, on_off):
        menu = ["MENULEFT", "MENURIGHT"]
        array = ["LEFT", "RIGHT", "B", "E", "C"]
        boo = False if on_off else True
        for item in menu:
            self.arrow_shortcut.get(item).setEnabled(boo)
        for item in array:
            self.analysis_Shortcut.get(item).setEnabled(on_off)

## Game Review Function End

## Voice Input Function

    def _apply_saved_voice_trigger_mode(self):
        try:
            self._voice_trigger_mode = str(self.settings.value("voice_trigger_mode", "toggle"))
        except Exception:
            self._voice_trigger_mode = "toggle"
        self._voice_trigger_mode = "toggle" if self._voice_trigger_mode.lower() == "toggle" else "hold"
        self._apply_voice_trigger_shortcuts()

    def _apply_voice_trigger_shortcuts(self):
        mode = "toggle" if str(self._voice_trigger_mode).lower() == "toggle" else "hold"
        self._voice_trigger_mode = mode
        if hasattr(self, "voice_input_shortcut"):
            self.voice_input_shortcut.setEnabled(mode == "toggle")
        if hasattr(self, "chatbotWidget") and self.chatbotWidget:
            self.chatbotWidget.update_voice_button_mode(mode)

    def _interrupt_tts_for_voice_input(self):
        try:
            if getattr(self, "tts_thread", None):
                self.tts_thread.interrupt_now(clear_queue=True)
        except Exception:
            pass

    def voice_input_press(self):
        if self._voice_trigger_mode != "hold":
            return
        self._interrupt_tts_for_voice_input()
        self._start_voice_input()

    def voice_input_release(self):
        if self._voice_trigger_mode != "hold":
            return
        self._stop_voice_input()

    def _start_voice_input(self):
        self._interrupt_tts_for_voice_input()

        if voice_input_thread.is_processing:
            print("Audio is being processed, please wait...")
            speak(t("speak.audio.processing_wait"))
            return

        if not voice_input_thread.press_event.is_set():
            print("Voice Input activated.")

       
            globals()["voice_input_mute_tts"] = True

            # Play voice recording sound
            sound_path = self._get_resource_path(os.path.join("Components", "voiceRecording.wav"))
            self.tts_thread.play_sound(sound_path)

            QTimer.singleShot(600, self._really_start_recording)


    def _really_start_recording(self):

        voice_input_thread.press_event.set()
        print("Recording started.")


    def _stop_voice_input(self):
        if voice_input_thread.press_event.is_set():
            voice_input_thread.press_event.clear()
            print("Voice input End")
          
            globals()["voice_input_mute_tts"] = False
            # Play voice recording sound
            sound_path = self._get_resource_path(os.path.join("Components", "voiceRecording.wav"))
            self.tts_thread.play_sound(sound_path)

    def voice_input(self):
        print("Ctrl S is pressed")
   
        self._interrupt_tts_for_voice_input()

        if self._voice_trigger_mode == "hold":
            return
        if voice_input_thread.press_event.is_set():
            self._stop_voice_input()
        else:
            self._start_voice_input()

    def keyReleaseEvent(self, event):
        if (
            self._voice_trigger_mode == "hold"
            and event.key() == Qt.Key.Key_S
            and (event.modifiers() & Qt.KeyboardModifier.ControlModifier)
        ):
            self._stop_voice_input()
            event.accept()
            return
        super().keyReleaseEvent(event)

    def check_action(self, str):
        match(str):
            case "options":
                self.helper_menu()
            case "computer":
                self.playWithComputerHandler()
            case "online":
                self.playWithOtherButtonHandler()
            case "puzzle":
                self.puzzleModeHandler()
            case "move":
                self._execute_user_move(voice_input_thread.chess_move, source="voice")
            case "resign":
                self.resign_handler()
            case "open_settings":
                self.openSettingMenu()
            case _:
                if (self.game_flow_status != Bot_flow_status.select_status and self.game_flow_status != Bot_flow_status.game_play_status):
                    self.game_play_mode = Game_play_mode.online_mode
                    layout = self.rightWidget.layout()
                    unhidden_widgets = []
                    for i in range(layout.count()):
                        widget = layout.itemAt(i).widget()
                        if widget and not widget.isHidden():
                            unhidden_widgets.append(widget)
                    for item in unhidden_widgets:
                        item.hide()
                    self.leftWidget.chessWebView.loadFinished.connect(lambda: QTimer.singleShot(2000, lambda: self.online_select_timeControl(str, skip=True)))
                    self.leftWidget.chessWebView.load(QUrl("https://www.chess.com/play/online"))
                else:
                    self.online_select_timeControl(str)

    def currentOption(self):
        match self.main_flow_status:
            case Bot_flow_status.setting_status:
                print("Choose the game mode that you want to play")

    def keyPressEvent(self, event):
        key = event.key()
        if (
            self._voice_trigger_mode == "hold"
            and key == Qt.Key.Key_S
            and (event.modifiers() & Qt.KeyboardModifier.ControlModifier)
        ):
            self._start_voice_input()
            event.accept()
            return
        if key in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_E, Qt.Key.Key_B):
            self.keyPressed_Signal.emit(event.key())
            return
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            try:
                focused = self.focusWidget()
                if focused and hasattr(focused, "isCheckable") and focused.isCheckable():
                    focused.setChecked(True)
                    if (
                        self.main_flow_status == Bot_flow_status.select_status
                        and self.game_play_mode == Game_play_mode.computer_mode
                        and focused in self.rightWidget.bot_buttons_all
                    ):
                        self.select_bot_from_button(focused)
                        self.select_bot()
                    else:
                        focused.click()
                    event.accept()
                    return
            except Exception:
                pass

## load text to TTS queue
def speak(sentence, importance=False, dialog=False, announce=None):
    global previous_sentence
    global internal_speak_engine

    previous_sentence = sentence
    if internal_speak_engine:
        speak_thread.queue.put((sentence, importance))
    else:
        print("no speak engine")
        if(announce):
            print("announce move")
            speak_thread.queue.put((sentence, importance))

# Voice Input Thread to handle audio recording, speech-to-text, keyword extraction and trigger signals
class VoiceInput_Thread(QThread):
    '''
    Allow User using Voice Input by record user's audio, perform Speech to Text and
    determine which action to perform based on the text result
    '''

    action_signal = pyqtSignal(str)
    transcribed_signal = pyqtSignal(str)

    ##auto start and loop until application close
    def __init__(self):
        super(VoiceInput_Thread, self).__init__()

        self.press_event = Event()
        self.is_processing = False  
        self.processed_by_chatbot = False  

        self.text_output = ""
        self.daemon = True
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = 1024
        self.frames = []
        self.chess_move = []
        self.audio = None
        self.stream = None
        self.start()

    def run(self):
        while True:
            self.press_event.wait()
            if self.press_event.is_set():
                self.record()
            else:
                self._close_stream()

    def _ensure_stream(self):
        if self.audio is None:
            self.audio = pyaudio.PyAudio()
        if self.stream is None:
            self.stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK,
            )

    def _close_stream(self):
        try:
            if self.stream is not None:
                self.stream.stop_stream()
                self.stream.close()
        except Exception:
            pass
        self.stream = None
        try:
            if self.audio is not None:
                self.audio.terminate()
        except Exception:
            pass
        self.audio = None

    def record(self):
        print("Voice Input function running")
        self._ensure_stream()
        while self.press_event.is_set():
            try:
                data = self.stream.read(self.CHUNK, exception_on_overflow=False)
            except Exception as exc:
                print(f"Audio read failed: {exc}")
                break
            self.frames.append(data)
        if self.frames:
            print("Voice Input Ended")
         
            self.is_processing = True
            tmp_path = None
            try:
                tmp_path = Path("./tmp.wav")
                with wave.open(str(tmp_path), 'wb') as wf:
                    wf.setnchannels(self.CHANNELS)
                    wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
                    wf.setframerate(self.RATE)
                    wf.writeframes(b''.join(self.frames))
                self.frames=[]
                print("Sending audio to STT server...")
                self.text_output = self._transcribe_with_server(tmp_path)
                print(f"Speech to Text finished! Output: {self.text_output}")
              
                self.processed_by_chatbot = False
                if not self.text_output:
                    return
              
                try:
                  
                    self.transcribed_signal.emit(self.text_output)
                except Exception as exc:
                    print(f"Handle transcribed text failed: {exc}")
            except Exception as e:
                print(f"Error processing audio: {e}")
            finally:
            
                self.is_processing = False
                self.frames = []
                self._close_stream()
                try:
                    if tmp_path and tmp_path.exists():
                        tmp_path.unlink()
                except Exception:
                    pass
        else:
            self.frames = []
            self._close_stream()

    def _transcribe_with_server(self, path: Path) -> str:
        headers = {}
        if APP_API_KEY:
            headers["Authorization"] = f"Bearer {APP_API_KEY}"
        try:
            with path.open("rb") as wav_file:
                files = {"file": ("voice.wav", wav_file, "audio/wav")}
                response = requests.post(
                    STT_SERVER_URL,
                    files=files,
                    headers=headers,
                    timeout=60,
                )
            response.raise_for_status()
            data = response.json()
            text = data.get("text") if isinstance(data, dict) else None
            if text is None:
                text = data.get("result") if isinstance(data, dict) else None
            if text is None and isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
                text = data["data"].get("text")
            return str(text or "").lower()
        except requests.RequestException as exc:
            print(f"STT request failed: {exc}")
            try:
                speak(t("speak.audio.sr_server_unreachable"))
            except Exception:
                pass
        except ValueError as exc:
            print(f"STT response decode failed: {exc}")
        return ""
  

    def _fallback_to_ai(self):
        try:
            if hasattr(window, 'handle_transcribed_text'):
                self.processed_by_chatbot = True
             
                self.transcribed_signal.emit(self.text_output)
                return
        except Exception as e:
            print(f"fallback to ai failed: {e}")

     
        speak(t("speak.chat.delegate_to_ai_wait"))

    def checkAction(self):
        print(f"Current main_flow_status: {window.main_flow_status}")
        ##Check voice instruction
        if(any(words in self.text_output for words in determinant.quit_application_words.value)):
            sys.exit()

        if(any(words in self.text_output for words in determinant.options_words.value)):
            self.action_signal.emit("options")

        if("setting" in self.text_output or "settings" in self.text_output):
            QTimer.singleShot(0, lambda: self.action_signal.emit("open_settings"))

        if(window.main_flow_status == Bot_flow_status.setting_status):
            if(any(words in self.text_output for words in determinant.computer_mode_words.value)):
                self.action_signal.emit("computer")

            elif(any(words in self.text_output for words in determinant.online_mode_words.value)):
                self.action_signal.emit("online")

            elif(any(words in self.text_output for words in determinant.puzzle_mode_words.value)):
                self.action_signal.emit("puzzle")

        elif(window.main_flow_status == Bot_flow_status.select_status):
            match window.game_play_mode:
                case Game_play_mode.computer_mode:
             
                    self._fallback_to_ai()
                case Game_play_mode.online_mode:
               
                    self._fallback_to_ai()
                case Game_play_mode.puzzle_mode:
               
                    self._fallback_to_ai()

        elif(window.main_flow_status == Bot_flow_status.game_play_status):
            match window.game_play_mode:
                case Game_play_mode.puzzle_mode:
                    self.voiceToMove()
                case _:
                    if(any(words in self.text_output for words in determinant.resign_words.value)):
                        self.action_signal.emit("resign")
                    else:
                        self.voiceToMove()
            
        else:
            
            self._fallback_to_ai()

    def voiceToMove(self):
        self.chess_move = []
        self.chess_order = []
        for moves in window.chess_position:
            if moves in self.text_output:
                self.chess_move.append(moves)
                self.chess_order.append(self.text_output.find(moves))
                print(f"move: {moves}")
        print(f"chess move = {self.chess_move}")
        if(len(self.chess_move)==2):
            print(self.chess_move[0], self.chess_move[1])
            if(self.chess_order[0]<self.chess_order[1]):
                self.chess_move = "".join(self.chess_move[0] + self.chess_move[1])
            else:
                self.chess_move = "".join(self.chess_move[1] + self.chess_move[0])
            print(f"chess move: {self.chess_move}")
            print("move triggered")
            self.action_signal.emit("move")
        else:
            speak(t("speak.login.invalid_input"))

if __name__ == "__main__":
    # Ensure consistent coordinate mapping on high-DPI / laptop screens (Windows)
    def _enable_windows_dpi_awareness():
        if sys.platform != "win32":
            return
        try:
            import ctypes
            # Per-monitor DPI awareness v2 (best)
            ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
            return
        except Exception:
            pass
        try:
            import ctypes
            # Per-monitor DPI awareness (Win8.1+)
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
            return
        except Exception:
            pass
        try:
            import ctypes
            # System DPI awareness fallback
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    _enable_windows_dpi_awareness()

    global speak_thread
    global voice_input_thread
    global current_dir
    global previous_sentence
    previous_sentence = ""

    current_dir = str(BASE_DIR)

    
    ffmpeg_dir = str(BASE_DIR / 'ffmpeg' / 'bin')
    my_env = os.environ
    my_env['PATH'] = f"{ffmpeg_dir}{os.pathsep}{my_env['PATH']}"

    speak_thread = TTSThread()  #activate TTS module
    voice_input_thread = VoiceInput_Thread()  #activate S2T module
    voice_input_mute_tts = False

    def speak(text, important=False, dialog=False, announce=None):
        global previous_sentence

        previous_sentence = "" if text is None else str(text)
        engine_enabled = globals().get("internal_speak_engine", True)

        
        if globals().get("voice_input_mute_tts", False):
            return

        if engine_enabled:
            speak_thread.queue.put((previous_sentence, important))
        else:
            print("no speak engine")
            if announce:
                print("announce move")
                speak_thread.queue.put((previous_sentence, important))

    speak = speak  # define speak function

    # print(my_env)

    app = QApplication(sys.argv)

    font = QFont()
    font.setPointSize(22)
    app.setFont(font)
    app.setApplicationName("Chess Bot")

    window = MainWindow()


    icon = QIcon(str(BASE_DIR / "Resources" / "Logo" / "chessBot_logo.png"))
    window.setWindowIcon(icon)

    
    window.show()

    window.leftWidget.chessWebView.page().setWebChannel(window.leftWidget.chessWebView.page().webChannel())
    window.leftWidget.chessWebView.page().setInspectedPage(window.leftWidget.chessWebView.page())

    def welcome_callback():
        if getattr(window, "_audio_reminder_confirmed", False):
            window._speak_welcome_message()
        else:
            window._welcome_pending = True
        window.leftWidget.chessWebView.loadFinished.disconnect()

    window.leftWidget.chessWebView.loadFinished.connect(welcome_callback)           

    window.move(10, 10)
    # window.switch_arrow_mode()
    sys.exit(app.exec())
