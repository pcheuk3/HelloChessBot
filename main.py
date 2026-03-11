import sys
import os
import re
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
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from PyQt6.QtCore import QUrl, Qt, QTimer, QThread, pyqtSignal, QSettings
from PyQt6.QtGui import QFont, QShortcut, QKeySequence, QIcon, QGuiApplication


import Components.js_function as js_function    ## header file
from Components.piece_move_component import widgetDragDrop, widgetClick
from Components.chess_validation_component import ChessBoard
from Components.speak_component import TTSThread
from ui.chatbot_window import ChatbotWindow
from ui.left_widget import LeftWidget
from ui.right_widget import RightWidget
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
    timeControlDeterminant_Type,
    timeControlDeterminant_Speak,
    chatbot_response,
)

import pyaudio
import wave
import whisper
import torch

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
    
class SettingMenu(QDialog):
    @staticmethod
    def _normalize_volume_to_slider_value(volume) -> int:
        """
        Accept either 0.0-1.0 float volume or 0-100 percent volume.
        Always return an int in [0, 100] for QSlider.
        """
        try:
            v = float(volume)
        except (TypeError, ValueError):
            v = 0.7

        if v <= 1.0:
            v *= 100.0
        v = round(v)
        return int(max(0, min(100, v)))

    @staticmethod
    def _normalize_rate_to_slider_value(rate) -> int:
        try:
            r = float(rate)
        except (TypeError, ValueError):
            r = 50.0
        r = round(r)
        return int(max(0, min(100, r)))

    def __init__(self, parent=None, rate=50, volume=0.7, engine=True, language: str = "en", font_size=22):
        super().__init__(parent)
        self._language_value = str(language or "en")
        # Set window title and size
        self.setWindowTitle(t("Setting"))
        # self.setGeometry(200, 200, 400, 200)
        self.setMinimumSize(500, 500)
        
        # Create layout
        layout = QVBoxLayout()
        language_layout = QHBoxLayout()
        rate_layout = QHBoxLayout()
        volume_layout = QHBoxLayout()
        font_size_layout = QHBoxLayout()

        # Language dropdown
        self.language_label = QLabel(t("Language"))
        self.language_label.setMinimumWidth(100)
        self.language_combo = CustomComboBox()
        self.language_combo.setAccessibleName(t("Language"))
        self.language_combo.setAccessibleDescription(t("Use up and down arrow keys to change the language"))
        self.language_combo.addItem(t("English"), "en")
        self.language_combo.addItem(t("Traditional Chinese"), "zh-TW")
        self.language_combo.addItem(t("Simplified Chinese"), "zh-CN")
        idx = self.language_combo.findData(self._language_value)
        if idx >= 0:
            self.language_combo.setCurrentIndex(idx)
        
        # bind the speech hint: read the current option when the option is changed
        self.language_combo.highlighted.connect(lambda idx: speak(self.language_combo.itemText(idx)))
        self.language_combo.currentIndexChanged.connect(lambda idx: speak(f"{t('Language')} set to {self.language_combo.itemText(idx)}"))

        language_layout.addWidget(self.language_label)
        language_layout.addWidget(self.language_combo)
        layout.addLayout(language_layout)

        # Create checkbox
        self.engine_value = engine
        self.screen_reader_checkBox = QCheckBox(t("Use built-in speech engine"))
        self.screen_reader_checkBox.setChecked(engine)
        self.screen_reader_checkBox.setAccessibleName(t("Use built-in speech engine"))
        self.screen_reader_checkBox.setAccessibleDescription(
            t("Use built-in speech engine to speak the text")
        )
        layout.addWidget(self.screen_reader_checkBox)

        # Create font size slider
        self.font_size_label = QLabel(t("Font Size"))
        self.font_size_label.setMinimumWidth(100)

        self.font_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_size_slider.setMinimum(10)
        self.font_size_slider.setMaximum(40)
        self.font_size_slider.setValue(int(font_size))
        self.font_size_slider.setTickPosition(QSlider.TickPosition.TicksRight)
        self.font_size_slider.setTickInterval(5)
        self.font_size_slider.setAccessibleName(t("Font Size"))
        self.font_size_slider.setAccessibleDescription(t("Use left and right arrow keys to adjust the font size of the text"))

        self.font_size_value_label = QLabel()
        self.font_size_value_label.setText(str(int(font_size)))

        font_size_layout.addWidget(self.font_size_label)
        font_size_layout.addWidget(self.font_size_slider)
        font_size_layout.addWidget(self.font_size_value_label)
        layout.addLayout(font_size_layout)
        
        # Create slider
        self.rate_label = QLabel(t("Speech Rate"))
        self.rate_label.setMinimumWidth(100)

        self.speech_rate_slider = QSlider(Qt.Orientation.Horizontal)
        self.speech_rate_slider.setMinimum(0)
        self.speech_rate_slider.setMaximum(100)
        rate_slider_value = self._normalize_rate_to_slider_value(rate)
        self.speech_rate_slider.setValue(rate_slider_value)
        self.speech_rate_slider.setTickPosition(QSlider.TickPosition.TicksRight)
        self.speech_rate_slider.setTickInterval(10)
        self.speech_rate_slider.setAccessibleName(t("Speech Rate"))
        self.speech_rate_slider.setAccessibleDescription(t("Use left and right arrow keys to adjust the speech rate of the text"))

        self.speech_rate_value_label = QLabel()
        self.speech_rate_value_label.setText(str(rate_slider_value))

        rate_layout.addWidget(self.rate_label)
        rate_layout.addWidget(self.speech_rate_slider)
        rate_layout.addWidget(self.speech_rate_value_label)


        self.volume_label = QLabel(t("Speech Volume"))
        self.volume_label.setMinimumWidth(100)  # Set minimum width for consistent alignment

        self.speech_volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.speech_volume_slider.setMinimum(0)
        self.speech_volume_slider.setMaximum(100)
        volume_slider_value = self._normalize_volume_to_slider_value(volume)
        self.speech_volume_slider.setValue(volume_slider_value)
        self.speech_volume_slider.setTickPosition(QSlider.TickPosition.TicksRight)
        self.speech_volume_slider.setTickInterval(10)
        self.speech_volume_slider.setAccessibleName(t("Speech Volume"))
        self.speech_volume_slider.setAccessibleDescription(t("Use left and right arrow keys to adjust the speech volume of the text"))

        self.volume_value_label = QLabel()
        self.volume_value_label.setText(str(volume_slider_value))

        volume_layout.addWidget(self.volume_label)
        volume_layout.addWidget(self.speech_volume_slider)
        volume_layout.addWidget(self.volume_value_label)

        # Connect slider value change to update label
        self.font_size_slider.valueChanged.connect(self.font_size_changed)
        self.speech_rate_slider.valueChanged.connect(self.rate_changed)
        self.speech_volume_slider.valueChanged.connect(self.volume_changed)
        self.screen_reader_checkBox.stateChanged.connect(self.checkBoxStateChanged)
                
        layout.addLayout(rate_layout)
        layout.addLayout(volume_layout)
        
        # Create OK button to close the dialog
        ok_button = CustomButton("OK")
        ok_button.setAccessibleName("OK")
        ok_button.setAccessibleDescription(t("OK button"))
        ok_button.clicked.connect(self.OK_pressed)
        layout.addWidget(ok_button)

        self.setting_layout = []
        self.setting_layout.append(self.language_combo) 
        self.setting_layout.append(self.screen_reader_checkBox)
        self.setting_layout.append(self.font_size_slider)
        self.setting_layout.append(self.speech_rate_slider)
        self.setting_layout.append(self.speech_volume_slider)
        self.setting_layout.append(ok_button)
        
        # Set layout
        self.setLayout(layout)

        self.currentfocus = 0 # start from the first one

        tab = QShortcut(QKeySequence("tab"), self)
        tab.activated.connect(self.tabHandler)

    def checkBoxStateChanged(self, state):
        print(state)
        if state == 2:
            self.engine_value = True
            speak("Turn on speak engine")
        else:
            self.engine_value = False
            speak("Turn off speak engine")

    def get_engine_value(self):
        return self.engine_value

    def get_language_value(self) -> str:
        return str(self.language_combo.currentData() or "en")

    def OK_pressed(self):
        speak("User Preference Saved")
        self.accept()

    def font_size_changed(self, value):
        speak(str(value))
        self.font_size_value_label.setText(str(value))

    def rate_changed(self, value):
        speak(str(value))
        self.speech_rate_value_label.setText(str(value))
    
    def volume_changed(self, value):
        speak(str(value))
        self.volume_value_label.setText(str(value))
        
    def get_rate_value(self):
        return self.speech_rate_slider.value()

    def get_font_size_value(self) -> int:
        return int(self.font_size_slider.value())
    
    def get_volume_value(self):
        return self.speech_volume_slider.value() / 100.0
    
    def tabHandler(self, arrow=None):
        print("tab")
        if(arrow == "down"):
            self.currentfocus -= 1
            if(self.currentfocus < 0):
                self.currentfocus = len(self.setting_layout) - 1
        else:
            self.currentfocus += 1
            if(self.currentfocus > len(self.setting_layout) - 1):
                self.currentfocus = 0
            self.setting_layout[self.currentfocus].setFocus()
        intro = self.setting_layout[self.currentfocus].accessibleDescription()
        speak(intro)

class confirmDialog(QDialog):
    """confirm popup dialog that show and speak the message"""
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("Confirm Dialog"))
        QBtn = (
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        def dialog_helper_menu():
            speak("press enter to confirm. <> or press delete to cancel")

        self.layout = QVBoxLayout()
        message = "confirm " + message
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
            speak("Cancel")
            self.reject()

class MainWindow(QMainWindow):
    """
    Merge left and right widget, and act as middle man for communication\n
    Control the application status, implement functionality to left and right widget.\n
    Handle all logic operation
    """
    keyPressed_Signal = pyqtSignal(int)

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
        self.leftWidget.chessWebView.page().runJavaScript(jsCode, callback)
##JS to click on web view button
    def clickWebButton(
        self, displayTextList, index, finalCallback, retry
    ):  ##avoid double load finish
        if index >= len(displayTextList):
            print("click finished")
            # QTimer.singleShot(1000, finalCallback)
            finalCallback()
            # self.capture_screens
            # hot()
            return True

        def next_click(result):
            # 如果這一步有成功點到對應文字的按鈕，才進入下一步
            if result == displayTextList[index][1].lower():
                QTimer.singleShot(
                    1000,
                    partial(
                        self.clickWebButton,
                        displayTextList,
                        index + 1,
                        finalCallback,
                        0,
                    ),
                )
                return

            # 超過一定次數仍然沒點到對應按鈕，就視為失敗，不再誤判為成功
            if retry >= 6:
                print(
                    f"clickWebButton failed: selector={displayTextList[index][0]}, text={displayTextList[index][1]}"
                )
                try:
                    speak("Web button not found, action cancelled")
                except Exception:
                    pass
                return

            # 否則重試當前這一步
            add = retry + 1
            QTimer.singleShot(
                500,
                partial(
                    self.clickWebButton,
                    displayTextList,
                    index,
                    finalCallback,
                    add,
                ),
            )

        # print(displayTextList[index][0], displayTextList[index][1].lower())
        selector = displayTextList[index][0]
        target_text = displayTextList[index][1].lower()

        if len(displayTextList[index]) == 3:
            # 嚴格匹配：文字/aria-label/data-* 等於目標文字（用於 "resign" 這類明確按鈕）
            jsCode = """
            function out() {{
                let buts = document.querySelectorAll('{0}');
                for (const but of buts) {{
                    const text = (but?.textContent || but?.innerText || '').trim().toLowerCase();
                    const aria = (but?.getAttribute('aria-label') || '').trim().toLowerCase();
                    const dataCy = (but?.getAttribute('data-cy') || '').trim().toLowerCase();
                    if (text === '{1}' || aria === '{1}' || dataCy === '{1}' || dataCy.includes('{1}')) {{
                        but.click();
                        console.error('clicked button for: {1}');
                        console.error('text=', text, 'aria=', aria, 'data-cy=', dataCy);
                        return '{1}';
                    }}
                }}
                return false;
            }}
            out();
            """.format(
                selector, target_text
            )
        else:
            # 寬鬆匹配：只要包含目標文字或 aria-label / data-* 中包含關鍵字即可
            jsCode = """
                function out() {{
                    let buts = document.querySelectorAll('{0}');
                    for (const but of buts) {{
                        const text = (but?.textContent || but?.innerText || '').trim().toLowerCase();
                        const aria = (but?.getAttribute('aria-label') || '').trim().toLowerCase();
                        const dataCy = (but?.getAttribute('data-cy') || '').trim().toLowerCase();
                        if (text.includes('{1}') || aria.includes('{1}') || dataCy.includes('{1}')) {{
                            but.click();
                            console.error('clicked button for: {1}');
                            console.error('text=', text, 'aria=', aria, 'data-cy=', dataCy);
                            return '{1}';
                        }}
                    }}
                    return false;
                }}
                out();
                """.format(
                selector, target_text
            )
        return self.leftWidget.chessWebView.page().runJavaScript(jsCode, next_click)

    def _show_audio_reminder_on_startup(self):
        title = "Audio Reminder"
        message = (
            "This software is designed for visually impaired users. "
            "Please ensure your system audio is enabled for voice guidance and assistance."
        )
        reminder_text = f"{message} Press Enter to confirm."
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
                Speak_template.welcome_sentense.value
                + Speak_template.game_intro_sentense.value,
                True,
            )
        except Exception:
            pass

    def _load_time_control_from_txt(self):
        """
        從 time_control.txt 讀取在線對戰的時間控制選項。
        檔案格式：
        catergory       selection name          js path
        Bullet          1 min                   document.querySelector("...")
        ...
        目前僅使用 category 與 selection name 來生成 UI（selection name 將作為按鈕文字，
        並在後續傳入 online_select_timeControl 使用）。js path 保留以便未來需要時擴充。
        """
        self.time_control_by_category = {}
        self.time_control_by_name = {}

        # 取得 Components 目錄下的 time_control.txt 路徑
        try:
            base_dir = os.path.dirname(__file__)
            txt_path = os.path.join(base_dir, "Components", "time_control.txt")
        except Exception as e:
            print(f"resolve time_control.txt path failed: {e}")
            return

        if not os.path.exists(txt_path):
            print(f"time_control.txt not found at {txt_path}")
            return

        # 根據空白與對齊解析三個欄位：類別、名稱、js 路徑
        line_pattern = re.compile(r"^(\S+)\s+(.+?)\s{2,}(.+)$")

        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            print(f"read time_control.txt failed: {e}")
            return

        # 跳過第一行表頭
        for raw in lines[1:]:
            line = raw.strip()
            if not line:
                continue
            m = line_pattern.match(line)
            if not m:
                continue
            category, name, js_expr = m.groups()
            self.time_control_by_category.setdefault(category, []).append(
                {"name": name, "js": js_expr}
            )
            # 若名稱重覆，後者覆蓋前者即可
            self.time_control_by_name[name] = {"category": category, "js": js_expr}

        # 載入完成後，將第一頁類別按鈕文字維持為 Bullet/Blitz/Rapid/Daily，
        # 第二頁具體選項的文字在打開某個類別時再動態填入。

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
                speak(f"login success! Username: {self.userLoginName}")
            else:
                print("The username or password is incorrect. Please try again")
                speak("The username or password is incorrect. Please try again")

        username = self.rightWidget.loginAccount_Input.text()
        password = self.rightWidget.loginPassword_Input.text()
        print(f"username: {username}")
        print(f"password: {password}")
        self.rightWidget.loginAccount_Input.clear()
        self.rightWidget.loginPassword_Input.clear()
        if(username == "" or password == ""):
            print("Invalid Input")
            speak("Invalid Input")
            return
        self.leftWidget.chessWebView.page().runJavaScript(js_function.userLogin + f"userLogin('{username}', '{password}')")
        speak("trying to login")
        QTimer.singleShot(3000, lambda: self.leftWidget.chessWebView.page().runJavaScript(js_function.loginSuccess, checkLogin))

    # User Logout
    def logout(self):
        print("Logging out...")
        speak("Logging out")
        
        profile = self.leftWidget.chessWebView.page().profile()
        # clear all cookies (this will clear the login status)
        profile.cookieStore().deleteAllCookies()
        # clear local storage (LocalStorage / IndexedDB etc.)
        profile.clearHttpCache()
        # clear the visited links
        profile.clearAllVisitedLinks()

        def performLogoutUI():
            """update the UI after logout"""
            # hide the logout button
            self.rightWidget.logoutButton.hide()
            
            # show the login button
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
            
            # if the login button is not in the layout, add it to the layout
            # find the logout button in the layout and insert the login button before it
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
            
            # 切换到设置状态
            self.change_main_flow_status(Bot_flow_status.setting_status)
            
            print("Logout successful")
            speak("Logout successful")
            
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
        
        # 等待 Cookie 清除完成后再更新 UI 和重新加载页面
        # deleteAllCookies() 是异步的，需要等待完成
        QTimer.singleShot(500, performLogoutUI)

    ##change the application flow status and re-init / clean the variable
    def change_main_flow_status(self, status):
        print("change status", status)
        match status:
            case Bot_flow_status.login_status:
                speak("Activate Login Phase, Please input your username and password")
                self.leftWidget.chessWebView.load(QUrl("https://www.chess.com/login"))
                self.main_flow_status = Bot_flow_status.login_status
                self.currentFocus = len(self.rightWidget.login_menu) - 1
                for item in self.rightWidget.setting_menu:
                    item.hide()
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
                self.rightWidget.colorBox.setText("Assigned Color: ")
                self.userColor = None
                self.opponentColor = None
                self.category_combobox = None
                self.bot_retry = False
                self.rightWidget.right_layout = self.rightWidget.setting_layout
                self.rightWidget.opponentBox.setText("Opponent move: \n")
                try:
                    for i in range(8):
                        for j in range(8):
                            if(isinstance(self.leftWidget.grids[i][j], QLabel)):
                                self.leftWidget.grids[i][j].deleteLater()
                except:
                    print("No grids need to delete")
                for item in range(self.rightWidget.setting_layout.count()):
                    self.rightWidget.setting_layout.itemAt(item).widget().hide()
                for item in self.rightWidget.setting_menu:
                    item.show() 
                self.currentFocus = len(self.rightWidget.setting_menu) - 1
                return
                
            case Bot_flow_status.select_status:
                self.main_flow_status = Bot_flow_status.select_status
                self.game_flow_status = Game_flow_status.not_start
                for item in self.rightWidget.setting_menu:
                    item.hide()
                match self.game_play_mode:
                    case Game_play_mode.computer_mode:
                        self.currentFocus = len(self.rightWidget.bot_category_select_menu)
                        for item in self.rightWidget.bot_category_select_menu:
                            item.show()
                        self.leftWidget.chessWebView.page().runJavaScript(js_function.open_bot_menu)
                        speak("Select bot category")
                    case Game_play_mode.online_mode:
                        # 進入在線對戰：第一頁先顯示時間控制類別按鈕
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
                for item in range(self.rightWidget.setting_layout.count()):
                    self.rightWidget.setting_layout.itemAt(item).widget().hide()
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
                # 僅在線上對戰模式顯示「剩餘時間 / Check Time」按鈕
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
                self.rightWidget.whitePieces.setText("White pieces: ")
                self.rightWidget.blackPieces.setText("Black pieces: ")
                self.input_mode = Input_mode.command_mode
                self.chessBoard = None
                for item in range(self.rightWidget.setting_layout.count()):
                    self.rightWidget.setting_layout.itemAt(item).widget().hide()
                for item in self.rightWidget.game_end_menu:
                    item.show()
                self.currentFocus = len(self.rightWidget.game_end_menu) - 1
                self.main_flow_status = Bot_flow_status.game_end_status

            case Bot_flow_status.puzzle_end_status:
                self.arrow_mode_switch(False)
                self.input_mode = Input_mode.command_mode
                self.main_flow_status = Bot_flow_status.puzzle_end_status
                for item in range(self.rightWidget.setting_layout.count()):
                    self.rightWidget.setting_layout.itemAt(item).widget().hide()
                for item in self.rightWidget.puzzle_end_menu:
                    item.show()
                self.currentFocus = len(self.rightWidget.puzzle_end_menu)

    ##change the application game mode
    def change_game_mode(self, mode):
        match mode:
            case None:
                self.game_play_mode = None
            case Game_play_mode.analysis_mode:
                self.currentFocus = len(self.rightWidget.analysis_menu) - 1
                self.game_play_mode = Game_play_mode.analysis_mode
                for item in range(self.rightWidget.setting_layout.count()):
                    self.rightWidget.setting_layout.itemAt(item).widget().hide()
                for item in self.rightWidget.analysis_menu:
                    item.show()

    ##initialize a vs computer game for user
    def playWithComputerHandler(self):
        if self.main_flow_status == Bot_flow_status.board_init_status:
            speak("Still " + Speak_template.initialize_game_sentense.value, True)
            return
        if (
            self.main_flow_status == Bot_flow_status.game_play_status
            and not self.game_flow_status == Game_flow_status.game_end
        ):
            speak("Please resign before start a new game", True)
            return
        print("computer mode selected")
        self.game_play_mode = Game_play_mode.computer_mode
        speak(
            "computer engine mode <>" + Speak_template.initialize_game_sentense.value,
            True,
        )
        self.leftWidget.chessWebView.loadFinished.connect(lambda: QTimer.singleShot(4000, self.checkExistGame))

        self.leftWidget.chessWebView.load(
            QUrl("https://www.chess.com/play/computer")
        )

    ##initialize a vs online player game for user
    def playWithOtherButtonHandler(self):  ###url
        if self.main_flow_status == Bot_flow_status.board_init_status:
            speak("Still " + Speak_template.initialize_game_sentense.value, True)
            return
        if (
            self.main_flow_status == Bot_flow_status.game_play_status
            and not self.game_flow_status == Game_flow_status.game_end
        ):
            speak("Please resign before start a new game", True)
            return
        print("online mode selected")
        speak(
            "online player mode <>" + Speak_template.initialize_game_sentense.value,
            True,
        )
        self.game_play_mode = Game_play_mode.online_mode
        self.leftWidget.chessWebView.loadFinished.connect(lambda: QTimer.singleShot(3000, self.checkExistGame))
        self.leftWidget.chessWebView.load(QUrl("https://www.chess.com/play/online"))

    def selectPanelHandler(self):
        input = self.rightWidget.selectPanel.text().lower()
        if(self.game_play_mode == Game_play_mode.computer_mode):
            print("no idea")
        elif(self.game_play_mode == Game_play_mode.online_mode):
            for selection in timeControlDeterminant_Type:
                if input in selection.value:
                    self.online_select_timeControl(selection.value[input])
    
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
                elif retry < 20:
                    if self.main_flow_status == Bot_flow_status.game_play_status and self.chessBoard is not None:
                        self.online_game_started = True
                        return
                    QTimer.singleShot(1000, lambda: poll_online_game_ready(None, retry + 1))
                else:
                    print("online game not ready in time")
                    speak("Match not started yet. Please select a time control again.")
                    self.online_game_started = False
                    self.change_main_flow_status(Bot_flow_status.select_status)

            self.leftWidget.chessWebView.page().runJavaScript(js_function.onlineGameReady, ready_callback)

        print(f"timeControl = {timeControl}")
        self.timeControl = timeControl
        self.online_game_started = False

        if(skip):
            self.leftWidget.chessWebView.loadFinished.disconnect()

        for item in self.rightWidget.online_mode_select_menu:
            item.hide()

        for item in self.rightWidget.play_menu:
            item.show()
        if self.userLoginName != None:
            print("login name", self.userLoginName)
            self.leftWidget.chessWebView.page().runJavaScript(js_function.clickTimeControlButton + f"clickTimeControlButton('{timeControl}', true)", poll_online_game_ready)
        else:
            print("No login")
            no_login_text = "No login detected. Continuing as guest mode."
            speak(no_login_text)
            self._append_chatbot_system_message(no_login_text)
            self.leftWidget.chessWebView.page().runJavaScript(js_function.clickTimeControlButton + f"clickTimeControlButton('{timeControl}', false)", poll_online_game_ready)

    #handle select bot
    def select_bot(self):
        def callback1(x):
            print("select bot")
            if(self.bot_retry):
                QTimer.singleShot(1000, lambda: self.leftWidget.chessWebView.page().runJavaScript(js_function.select_bot + f"select_bot('{self.category_combobox.currentText()}');"))
                QTimer.singleShot(2000, lambda: self.leftWidget.chessWebView.page().runJavaScript(js_function.check_bot_locked, callback2))
                return
            QTimer.singleShot(1000, lambda: self.leftWidget.chessWebView.page().runJavaScript(js_function.check_bot_locked, callback2))

        def callback2(locked):
            print(f"locked = {locked}")
            if(locked):
                # self.leftWidget.chessWebView.load(
                #     QUrl("https://www.chess.com/play/computer")
                # )
                speak("The bot is locked for guest or non-premium account. Please select another bot.")
                self.bot_retry = True
            else:
                self.category_combobox.hide()
                self.rightWidget.play_button.hide()
                self.rightWidget.back_to_category_button.hide()
                for item in self.rightWidget.play_menu:
                    item.show()
                board()
                speak("Bot game Started")

        def board():
            self.getColor()
            self.initBoard()
            self.getBoard()

        print(f"Bot: {self.category_combobox.currentText()}")
        if(self.category_combobox == self.rightWidget.combobox_engine):
            level = self.category_combobox.currentText().split()[1]
            print(level)
            self.leftWidget.chessWebView.page().runJavaScript(js_function.select_engine_level + f"select_engine_level('{level}');", callback1)
            return
        
        self.leftWidget.chessWebView.page().runJavaScript(js_function.select_bot + f"select_bot('{self.category_combobox.currentText()}');", callback1)

    #handle select bot category
    def bot_select_category(self, category):
        for item in self.rightWidget.bot_category_select_menu:
            item.hide()
        match category:
            case "coach":
                self.category_combobox = self.rightWidget.combobox_coach
            case "adaptive":
                self.category_combobox = self.rightWidget.combobox_adaptive
            case "beginner":
                self.category_combobox = self.rightWidget.combobox_beginner
            case "intermediate":
                self.category_combobox = self.rightWidget.combobox_intermediate
            case "advanced":
                self.category_combobox = self.rightWidget.combobox_advanced
            case "master":
                self.category_combobox = self.rightWidget.combobox_master
            case "athletes":
                self.category_combobox = self.rightWidget.combobox_athletes
            case "musicians":
                self.category_combobox = self.rightWidget.combobox_musicians
            case "creators":
                self.category_combobox = self.rightWidget.combobox_creators
            case "top_players":
                self.category_combobox = self.rightWidget.combobox_top_players
            case "personalities":
                self.category_combobox = self.rightWidget.combobox_personalities
            case "engine":
                self.category_combobox = self.rightWidget.combobox_engine
        self.category_combobox.show()
        self.rightWidget.play_button.show()
        self.rightWidget.back_to_category_button.show()
        self.currentFocus = 3
        speak("Please first select the bot you want to play, then click play to start")

    #function for return to category selection
    def back_to_category(self):
        print("Return to Category")
        self.category_combobox.hide()
        self.rightWidget.play_button.hide()
        self.rightWidget.back_to_category_button.hide()
        for item in self.rightWidget.bot_category_select_menu:
            item.show()
        self.category_combobox = None
        self.currentFocus = len(self.rightWidget.bot_category_select_menu)

    #function to speak out selected bot
    def bot_information(self, index, select=False):
        print(index)
        if(select):
            print(index)
            print(f"{self.category_combobox.currentText()} is selected")
            speak(f"{self.category_combobox.currentText()} is selected")
            return
        # index = self.category_combobox.currentIndex()
        intro = self.category_combobox.itemData(index, Qt.ItemDataRole.AccessibleTextRole)
        speak(intro)

    #function to check whether unfinished game exist
    def checkExistGame(self):
        self.online_game_started = False

        def callback(moveList):
            print(f"movemovmeomvomeovmo = {moveList}")
            if(moveList):
                self.change_main_flow_status(Bot_flow_status.board_init_status)
                self.getColor(exist_game="Existing Game Founded. ")
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
                self.rightWidget.moveList.setText("Move List:\n" + self.moveListString)
        
                print(self.chessBoard.board_object)
                self.previous_game_exist = True
                turn = "WHITE" if(self.moveList_element %2==0) else "BLACK"
                print(f"current turn: {turn}")
                self.game_flow_status = Game_flow_status.user_turn if(turn==self.userColor) else Game_flow_status.opponent_turn
                print("Existing Game Founded")
                # 切換到遊戲進行狀態，但不再自動進行局面分析，
                # 由使用者按下「Current Game Analysis」按鈕時再觸發。
                self.change_main_flow_status(Bot_flow_status.game_play_status)
                return

            else:
                print("no existing board")
                self.change_main_flow_status(Bot_flow_status.select_status)


        try:
            self.leftWidget.chessWebView.loadFinished.disconnect()
        except TypeError:
            # 沒有已連接的 slot 時，PyQt 會拋 TypeError，這裡可安全忽略
            pass
        self.leftWidget.chessWebView.page().runJavaScript(js_function.checkExistGame, callback)

    def getPiecesLocation(self, location):
        self.rightWidget.whitePieces.setText(f"White pieces: " + location[0])
        self.rightWidget.blackPieces.setText(f"Black pieces: " + location[1])


## Puzzle Mode Start:

    def puzzleModeHandler(self):
        if(self.game_flow_status == Bot_flow_status.game_play_status):
            return
        speak(Speak_template.initialize_game_sentense.value, True)
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
        # Puzzle mode 不允許悔棋：隱藏悔棋按鍵（其他模式不受影響）
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
                        speak("You are playing as black.")
                        self.opponentColor = "WHITE"
                        self.currentPos = 'h8'
                        print(f"User: {self.userColor}, Oppoenent: {self.opponentColor}")
                
                try:
                    self.rightWidget.colorBox.setText("Assigned Color: " + self.userColor)
                    self.puzzle_mode_ConstructBoard()
                except:
                    speak("You have reach the puzzle limit for your account. Returning to home page.")
                    self.leftWidget.chessWebView.load(QUrl("https://www.chess.com"))
                    self.change_main_flow_status(Bot_flow_status.setting_status)
            else:
                match title:
                    case "Correct" | "Solved":
                        print("Correct")
                        speak("Correct. Please select next action.")
                        self.game_flow_status = self.change_main_flow_status(Bot_flow_status.puzzle_end_status)
                    #button click next
                    case "Incorrect":
                        print("Incorrect, puzzle run ended. Please select next action.")
                        speak("Incorrect, puzzle run ended. Please select next action.")
                        self.change_main_flow_status(Bot_flow_status.puzzle_end_status)
                    case _:
                        # self.puzzle_getOppMove_sgn.emit()
                        self.puzzle_mode_GetMove()

        self.leftWidget.chessWebView.page().runJavaScript(js_function.puzzle_mode_GetTitle, callback)

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
        self.leftWidget.chessWebView.page().runJavaScript(js_function.puzzle_mode_constructBoard, callback)

    def puzzle_mode_GetMove(self):
        def callback(uci_move):
            print(uci_move)
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
                speak(f"Opponent Last Move: {src} to {dest}")
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
            
            self.leftWidget.chessWebView.page().runJavaScript(js_function.getPiecesLocation, self.getPiecesLocation)

        if self.input_mode == Input_mode.arrow_mode:
            self.all_grids_switch(True)
        self.leftWidget.chessWebView.page().runJavaScript(js_function.puzzle_mode_GetOpponentMove, callback)

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
        QTimer.singleShot(500, lambda: self.leftWidget.chessWebView.page().runJavaScript(js_function.getPiecesLocation, self.getPiecesLocation))

    def clickNextPuzzle(self):
        def callback(x):
            self.userColor = None
            self.change_main_flow_status(Bot_flow_status.board_init_status)
            QTimer.singleShot(2000, self.puzzle_mode_InitBoard)

        self.leftWidget.chessWebView.page().runJavaScript(js_function.clickNextPuzzle, callback)

    def retryPuzzle(self):
        def callback(x):
            self.userColor = None
            self.change_main_flow_status(Bot_flow_status.board_init_status)
            QTimer.singleShot(2000, self.puzzle_mode_InitBoard)

        self.leftWidget.chessWebView.page().runJavaScript(js_function.retryPuzzle, callback)

## Puzzle Mode End

    ##convert move to human readable form
    def move_to_human_form(self, attackerColor, uciString, sanString):
        counter_color = "WHITE" if attackerColor == "BLACK" else "BLACK"
        human_string = attackerColor
        uciString = str(uciString).lower()
        sanString = str(sanString).lower()
        target_square = uciString[:2]
        dest_square = uciString[2:4]

        self.chessBoard.board_object.pop()

        en_passant = self.chessBoard.board_object.has_legal_en_passant()
        target_piece_type = self.chessBoard.check_grid(target_square).__str__().lower()

        dest_piece_type = self.chessBoard.check_grid(dest_square).__str__().lower()

        print(target_piece_type, dest_piece_type)
        # self.chessBoard.moveWithValidate(sanString)
        if sanString.count("x"):
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

        if sanString.count("O-O-O"):
            human_string = human_string + " queenside castling"
        elif sanString.count("O-O"):
            human_string = human_string + " kingside castling"
        elif sanString.count("="):
            human_string = (
                human_string
                + " and promoted to "
                + PIECE_TYPE_CONVERSION[
                    sanString[sanString.index("=") + 1].__str__().lower()
                ]
            )

        if sanString.count("+"):
            human_string = human_string + " and check "
        self.chessBoard.moveWithValidate(sanString)
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
        return self.leftWidget.chessWebView.page().runJavaScript(jsCode, callBack)

    ##click resign button on web view
    def resign_handler(self):
        dlg = confirmDialog("to resign from current game.")
        if dlg.exec():
            def callBack():
                # 只有在成功點擊完網頁上的按鈕序列後，才真正把狀態切成對局結束
                self.change_main_flow_status(Bot_flow_status.game_end_status)
                self.game_flow_status = Game_flow_status.game_end
                try:
                    if hasattr(self, 'chatbotWidget') and hasattr(self.chatbotWidget, 'add_system_bot_message'):
                        self.chatbotWidget.add_system_bot_message("Resigned the current game.")
                        self.chatbotWidget.add_system_bot_message("Press Tab to select the next option.")
                except Exception:
                    pass
                speak(Speak_template.user_resign.value)
                # 語音提示使用者用 Tab 選擇下一個選項
                speak("Press Tab to select the next option.")
                self.getOpponentMoveTimer.stop()
                self.getScoreTimer.start(1000)
                return

            if (
                self.userLoginName == None
                or self.game_play_mode == Game_play_mode.computer_mode
            ):
                self.clickWebButton(
                    [
                    ("#board-layout-sidebar > div > div.play-controller-component.sidebar-controller-component > div:nth-child(4) > div > div.primary-controls-topControls > button:nth-child(1)", "resign", True),
                    ("#board-layout-sidebar > div > div.play-controller-component.sidebar-controller-component > div:nth-child(4) > div > div.primary-controls-topControls > dialog > div > div > div.cc-confirmation-modal-buttons > button.cc-button-component.cc-button-danger.cc-button-large.cc-bg-danger", "resign", True),
                    ],
                    0,
                    callBack,
                    0,
                )
            else:
                self.clickWebButton(
                    [
                    ("#board-layout-sidebar > div > div.play-controller-component.sidebar-controller-component > div:nth-child(4) > div > div.primary-controls-topControls > button:nth-child(1)", "resign", True),
                    ("#board-layout-sidebar > div > div.play-controller-component.sidebar-controller-component > div:nth-child(4) > div > div.primary-controls-topControls > dialog > div > div > div.cc-confirmation-modal-buttons > button.cc-button-component.cc-button-danger.cc-button-large.cc-bg-danger", "resign", True),
                    ],
                    0,
                    callBack,
                    0,
                )
        else:
            speak("Cancel!")

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
            # 顯示彈窗：將清單格式化為人類可讀
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
            # 若近期由聊天機器人觸發了動作，優先將焦點回到聊天輸入欄
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
            if self.game_flow_status == Game_flow_status.user_turn:
                self.puzzle_movePiece(input)
            else:
                speak("Please wait for your opponent")
            self.rightWidget.commandPanel.clear()
            return
        
        match self.main_flow_status:
            # case Bot_flow_status.setting_status:
            #     if input == "computer":
            #         self.playWithComputerHandler()
            #         self.rightWidget.commandPanel.clear()
            #         return
            #     elif input == "online":
            #         self.playWithOtherButtonHandler()
            #         self.rightWidget.commandPanel.clear()
            #         return
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
                                    Speak_template.check_time_sentense.value.format(
                                        user, opponent
                                    )
                                )

                        self.leftWidget.checkTime(timeCallback)
                        self.rightWidget.commandPanel.clear()
                        return
                    else:
                        speak("No timer for computer mode")
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
                if self.game_flow_status == Game_flow_status.user_turn:
                    self.movePiece(input)
                else:
                    speak("Please wait for your opponent's move")

    def _append_chatbot_system_message(self, message: str):
        """
        將系統／錯誤訊息同步顯示到聊天機器人視窗中（若存在）。
        """
        if not message:
            return
        try:
            if hasattr(self, "chatbotWidget") and hasattr(self.chatbotWidget, "chat_display"):
                line = t("chat.bot_line", message=message)
                self.chatbotWidget.chat_display.append(line)
        except Exception:
            # 避免因聊天視窗問題影響主要流程
            pass
    def movePiece(self, input):  ## input store the move command
        if self.game_play_mode == Game_play_mode.online_mode and not self.online_game_started:
            speak("Game has not started yet. Please wait for matchmaking to finish.")
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
                        self.getOpponentMoveTimer.start(1000)
                        self.setMoveList(uci_string)
            else:
                self.chessBoard.board_object.pop()
                self.rightWidget.commandPanel.clear()
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
                    self.getOpponentMoveTimer.start(1000)
                    self.setMoveList(uci_string)
                    
            else:
                self.chessBoard.board_object.pop()
                self.rightWidget.commandPanel.clear()
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
        
        QTimer.singleShot(500, lambda: self.leftWidget.chessWebView.page().runJavaScript(js_function.getPiecesLocation, self.getPiecesLocation))

    ##check game end, sync with mirrored chess board and announce opponent's move
    def announceMove(self, sanString):
        print("broadcast move: ", sanString)
        if sanString == None or self.chessBoard == None:
            return False
        crawl_result = None
        check_win = self.chessBoard.detect_win()
        if not check_win == "No win detected.":  ##check user wins
            print(check_win)
            speak(check_win, announce=True)
            self.game_flow_status = Game_flow_status.game_end
            self.change_main_flow_status(Bot_flow_status.setting_status)
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
                    self.change_main_flow_status(Bot_flow_status.setting_status)
                    self.getOpponentMoveTimer.stop()
                    self.getScoreTimer.start(1000)
                    speak(crawl_result, True, announce=True)
                    return True
                else:
                    return False
            uci_string = movePair[0]
            san_string = movePair[1]

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
                    importance=True,
                    announce=True,
                )
                self.rightWidget.opponentBox.setText(
                    "Opponent move: \n" + human_string
                )
                self.game_flow_status = Game_flow_status.user_turn
                if not check_win == "No win detected.":
                    speak(check_win, True, announce=True)
                    self.game_flow_status = Game_flow_status.game_end
                    self.change_main_flow_status(Bot_flow_status.setting_status)
                    self.getOpponentMoveTimer.stop()
                    self.getScoreTimer.start(1000)
                if not crawl_result == None:
                    self.game_flow_status = Game_flow_status.game_end
                    self.change_main_flow_status(Bot_flow_status.setting_status)
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
        def callback(result):
            if result:
                self.game_flow_status = Game_flow_status.game_end
                self.change_main_flow_status(Bot_flow_status.game_end_status)
                self.getScoreTimer.start(1000)
                self.getOpponentMoveTimer.stop()
                print(result)
                speak(result, announce=True)

        if(self.game_play_mode == Game_play_mode.computer_mode):
            self.leftWidget.chessWebView.page().runJavaScript(js_function.checkGameEnd + 'checkGameEnd("computer");', callback)
        else:
            self.leftWidget.chessWebView.page().runJavaScript(js_function.checkGameEnd + 'checkGameEnd("online");', callback)

    ##JS to get opponent move SAN
    def getOpponentMove(self):
        if self.main_flow_status != Bot_flow_status.game_play_status:
            self.getOpponentMoveTimer.stop()
            return
        if self.game_play_mode == Game_play_mode.online_mode and not self.online_game_started:
            self.getOpponentMoveTimer.stop()
            return

        def callback(x):
            print(f"Opponent move = {x}")

            if self.main_flow_status != Bot_flow_status.game_play_status:
                self.getOpponentMoveTimer.stop()
                return
            if self.game_play_mode == Game_play_mode.online_mode and not self.online_game_started:
                self.getOpponentMoveTimer.stop()
                return

            if self.announceMove(x):
                self.getOpponentMoveTimer.stop()
                move = self.chessBoard.board_object.pop()
                self.setMoveList(move)
                self.chessBoard.board_object.push_uci(str(move))
                self.leftWidget.chessWebView.page().runJavaScript(js_function.getPiecesLocation, self.getPiecesLocation)
                # 对手走完后，同步一次网页端 FEN，确保 get fen 始终是最新
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

        self.leftWidget.chessWebView.page().runJavaScript(jsCode, callback)

    def _refresh_fen_from_web(self, reason: str = ""):
        """
        从 Chess.com 网页端抓取当前 FEN，并同步到镜像棋盘（用于 chatbot 的 get fen）。
        该方法是“尽力而为”：抓取失败不会影响主流程。
        """
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
            # 基本校验：标准 FEN 至少应包含 6 个字段
            if len(fen_value.split()) < 4:
                return
            try:
                self.chessBoard.board_object = chess.Board(fen_value)
                self._latest_web_fen = fen_value
                print(f"[FEN sync]{'['+reason+']' if reason else ''} {fen_value}")
            except Exception as exc:
                print(f"Web FEN sync failed: {exc}")

        def _after_share(_clicked):
            # 等待弹窗渲染出 share-fen 输入框
            QTimer.singleShot(450, lambda: page.runJavaScript(js_function.getFEN, _apply_fen))

        try:
            page.runJavaScript(js_function.clickShare, _after_share)
        except Exception:
            # share 按钮不存在或页面结构变化时，静默失败
            return

    ##JS to click on web view button
    def clickWebButton(
        self, displayTextList, index, finalCallback, retry
    ):  ##avoid double load finish
        if index >= len(displayTextList):
            print("click finished")
            # QTimer.singleShot(1000, finalCallback)
            finalCallback()
            # self.capture_screens
            # hot()
            return True

        def next_click(result):
            # 如果這一步有成功點到對應文字的按鈕，才進入下一步
            if result == displayTextList[index][1].lower():
                QTimer.singleShot(
                    1000,
                    partial(
                        self.clickWebButton,
                        displayTextList,
                        index + 1,
                        finalCallback,
                        0,
                    ),
                )
                return

            # 超過一定次數仍然沒點到對應按鈕，就視為失敗，不再誤判為成功
            if retry >= 6:
                print(
                    f"clickWebButton failed: selector={displayTextList[index][0]}, text={displayTextList[index][1]}"
                )
                try:
                    speak("Web button not found, action cancelled")
                except Exception:
                    pass
                return

            # 否則重試當前這一步
            add = retry + 1
            QTimer.singleShot(
                500,
                partial(
                    self.clickWebButton,
                    displayTextList,
                    index,
                    finalCallback,
                    add,
                ),
            )

        # print(displayTextList[index][0], displayTextList[index][1].lower())
        selector = displayTextList[index][0]
        target_text = displayTextList[index][1].lower()

        if len(displayTextList[index]) == 3:
            # 嚴格匹配：文字/aria-label/data-* 等於目標文字（用於 "resign" 這類明確按鈕）
            jsCode = """
            function out() {{
                let buts = document.querySelectorAll('{0}');
                for (const but of buts) {{
                    const text = (but?.textContent || but?.innerText || '').trim().toLowerCase();
                    const aria = (but?.getAttribute('aria-label') || '').trim().toLowerCase();
                    const dataCy = (but?.getAttribute('data-cy') || '').trim().toLowerCase();
                    if (text === '{1}' || aria === '{1}' || dataCy === '{1}' || dataCy.includes('{1}')) {{
                        but.click();
                        console.error('clicked button for: {1}');
                        console.error('text=', text, 'aria=', aria, 'data-cy=', dataCy);
                        return '{1}';
                    }}
                }}
                return false;
            }}
            out();
            """.format(
                selector, target_text
            )
        else:
            # 寬鬆匹配：只要包含目標文字或 aria-label / data-* 中包含關鍵字即可
            jsCode = """
                function out() {{
                    let buts = document.querySelectorAll('{0}');
                    for (const but of buts) {{
                        const text = (but?.textContent || but?.innerText || '').trim().toLowerCase();
                        const aria = (but?.getAttribute('aria-label') || '').trim().toLowerCase();
                        const dataCy = (but?.getAttribute('data-cy') || '').trim().toLowerCase();
                        if (text.includes('{1}') || aria.includes('{1}') || dataCy.includes('{1}')) {{
                            but.click();
                            console.error('clicked button for: {1}');
                            console.error('text=', text, 'aria=', aria, 'data-cy=', dataCy);
                            return '{1}';
                        }}
                    }}
                    return false;
                }}
                out();
                """.format(
                selector, target_text
            )
        return self.leftWidget.chessWebView.page().runJavaScript(jsCode, next_click)

    # ---- 在線對戰：時間控制多頁選單相關邏輯 ----

    def open_online_category_page(self):
        """
        第一頁：顯示 Bullet / Blitz / Rapid / Daily 四個類別按鈕，
        並在底部附上 Back to Home Page 與 Back to Previous Page（此頁返回上一頁無作用，可隱藏）。
        """
        self.current_timecontrol_category = None
        self.current_timecontrol_options = []
        self.selected_time_control_name = None

        # 進入選擇類別前，先在 Chess.com 頁面上，用和 resign 相同的機制，依照 js path 點兩個必要按鈕
        # 這裡只靠 selector，不檢查文字內容，因此文字欄位給空字串即可
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

        # 先隱藏所有在線模式相關按鈕
        for widget in self.rightWidget.online_mode_select_menu:
            widget.hide()

        # 顯示類別按鈕
        for btn in self.rightWidget.online_category_buttons.values():
            btn.show()

        # 類別頁不需要 Start Game 與 Back to Previous（上一頁），但需要回主頁
        self.rightWidget.online_start_game_button.hide()
        self.rightWidget.back_to_previous_page_button.hide()
        self.rightWidget.returnToHomePageButton.show()

        # 將焦點移至類別群組最後一個按鈕，方便鍵盤操作
        self.currentFocus = len(self.rightWidget.online_mode_select_menu) - 1
        try:
            speak("Select time control category")
        except Exception:
            pass

    def open_online_selection_page(self, category: str):
        """
        第二頁：根據選擇的類別，顯示對應的 selection name 按鈕，
        並在底部顯示 Back to Home Page、Back to Previous Page 以及 Start Game 按鈕。
        """
        self.current_timecontrol_category = category
        self.current_timecontrol_options = self.time_control_by_category.get(category, [])
        self.selected_time_control_name = None

        # 先隱藏所有在線模式相關按鈕
        for widget in self.rightWidget.online_mode_select_menu:
            widget.hide()

        # 動態填入最多 6 個 selection name
        for idx, btn in enumerate(self.rightWidget.online_selection_buttons):
            if idx < len(self.current_timecontrol_options):
                option = self.current_timecontrol_options[idx]
                btn.setText(option["name"])
                btn.show()
            else:
                btn.hide()

        # 底部功能按鈕
        self.rightWidget.back_to_previous_page_button.show()
        self.rightWidget.online_start_game_button.setEnabled(False)
        self.rightWidget.online_start_game_button.show()
        self.rightWidget.returnToHomePageButton.show()

        # 更新焦點位置
        self.currentFocus = len(self.rightWidget.online_mode_select_menu) - 1
        try:
            speak(f"Select {category} time control")
        except Exception:
            pass

    def handle_online_selection_button(self, index: int):
        """
        點擊第二頁的某一個時間控制按鈕：
        - 記錄選中的 selection name
        - 啟用 Start Game 按鈕
        """
        if not self.current_timecontrol_options:
            return
        if index < 0 or index >= len(self.current_timecontrol_options):
            return

        option = self.current_timecontrol_options[index]
        self.selected_time_control_name = option["name"]
        self.rightWidget.online_start_game_button.setEnabled(True)

        try:
            speak(f"{self.selected_time_control_name} selected. Press OK to start game.")
        except Exception:
            pass

    def start_online_game(self):
        """
        第二頁底部的 OK 按鈕：
        - 使用選中的 selection name 呼叫既有的 online_select_timeControl 邏輯
        - 之後再透過 js path 觸發 Chess.com 介面的實際 Start Game 按鈕
        """
        if not self.selected_time_control_name:
            return
        # 1) 依照提供的 js path，先點擊選中的時間控制按鈕
        selected = self.time_control_by_name.get(self.selected_time_control_name, {})
        selected_js_expr = selected.get("js")
        if selected_js_expr:
            try:
                jsCode = f"""
                (function() {{
                    try {{
                        const el = {selected_js_expr};
                        if (el) {{
                            el.click();
                            return "clicked";
                        }}
                        return "not_found";
                    }} catch (e) {{
                        console.error("time control js error", e);
                        return "error";
                    }}
                }})();
                """
                self.leftWidget.chessWebView.page().runJavaScript(jsCode)
            except Exception:
                pass
        else:
            # 若沒有 js path，退回原有流程
            self.online_select_timeControl(self.selected_time_control_name)

        # 2) 再點擊 Chess.com 的 Start Game 按鈕（不依賴 selection js path）
        try:
            self.clickWebButton(
                [
                    (
                        "#board-layout-sidebar > div.sidebar-content > div.new-game-component > div.new-game-primary > button",
                        "",
                    ),
                ],
                0,
                lambda: None,
                0,
            )
        except Exception:
            pass

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

            # 可能在頁面尚未渲染完成時拿到 None，延遲重試避免 TypeError
            if color is None:
                QTimer.singleShot(500, lambda: self.getColor(exist_game))
                return

            color = str(color)
            self.userColor = color
            self.rightWidget.colorBox.setText("Assigned Color: " + color)
            if color == "BLACK":
                self.opponentColor = "WHITE"
                self.row, self.col = 7, 7
                self.currentPos = 'h8'
                speak(exist_game + Speak_template.user_black_side_sentense.value)
                # 顏色播報後，查詢一次全盤棋子座標（更新 white/black pieces 顯示）
                QTimer.singleShot(150, lambda: self.leftWidget.chessWebView.page().runJavaScript(js_function.getPiecesLocation, self.getPiecesLocation))
                self.game_flow_status = Game_flow_status.opponent_turn
                self.getOpponentMoveTimer.start(1000)
            else:
                self.opponentColor = "BLACK"
                self.row, self.col = 0, 0
                self.currentPos = 'a1'
                speak(exist_game + Speak_template.user_white_side_sentense.value)
                # 顏色播報後，查詢一次全盤棋子座標（更新 white/black pieces 顯示）
                QTimer.singleShot(150, lambda: self.leftWidget.chessWebView.page().runJavaScript(js_function.getPiecesLocation, self.getPiecesLocation))
                self.game_flow_status = Game_flow_status.user_turn

        self.leftWidget.chessWebView.page().runJavaScript(js_function.getColor, callback)

    #JS to detect grid position and assign label reference
    def initBoard(self):
        def callback(coor):
            print(coor)
            x = coor[0]
            y = coor[1]
            dist = coor[2]
            print(f"INITBOARD COLOR: {self.userColor}")
            if(self.userColor == "WHITE"):
                for row in range(8):
                    for col in range(8):
                        label = QLabel(self)
                        label.setGeometry(int(x + col*dist), int(y - row*dist), int(dist*0.5), int(dist*0.5))
                        pos = list(CHESSBOARD_LOCATION_CONVERSION.keys())[list(CHESSBOARD_LOCATION_CONVERSION.values()).index(str(col+1))] + str(row+1)
                        # label.setText("  " + pos)
                        label.setAccessibleName(pos)
                        label.hide()
                        self.leftWidget.grids[col][row] = label
            else:
                for row in reversed(range(8)):
                    for col in reversed(range(8)):
                        label = QLabel(self)
                        label.setGeometry(int(x + (7-col)*dist), int(y - (7-row)*dist), int(dist*0.5), int(dist*0.5))
                        pos = list(CHESSBOARD_LOCATION_CONVERSION.keys())[list(CHESSBOARD_LOCATION_CONVERSION.values()).index(str(col+1))] + str(row+1)
                        # label.setText("  " + pos)
                        label.setAccessibleName(pos)
                        label.hide()
                        self.leftWidget.grids[col][row] = label

            self.leftWidget.chessWebView.page().runJavaScript(js_function.getPiecesLocation, self.getPiecesLocation)

        self.leftWidget.chessWebView.page().runJavaScript(js_function.getBoard, callback)

    ##switch to command mode
    def switch_command_mode(self):
        print("shortcut ctrl + F pressed")
        speak("command mode <> you can type your move here")
        self.arrow_mode_switch(False)
        self.input_mode = Input_mode.command_mode
        self.currentFocus = len(self.rightWidget.play_menu) - 1
        self.rightWidget.commandPanel.setFocus()

    ##switch to arrow mode, only allowd when game started
    def switch_arrow_mode(self):
        print("shortcut ctrl + J pressed")
        if self.main_flow_status == Bot_flow_status.game_play_status:

            speak("arrow_mode")
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
            unhidden_widgets = []
            # if self.main_flow_status == Bot_flow_status.login_status:
            #     unhidden_widgets = self.rightWidget.login_menu
            if self.game_play_mode == Game_play_mode.analysis_mode:
                unhidden_widgets = self.rightWidget.analysis_menu
                print(len(unhidden_widgets))
            else:
                # 改进：递归获取所有可聚焦的widgets
                def get_focusable_widgets(widget):
                    """递归获取所有可聚焦的widgets"""
                    widgets = []
                    if widget is None:
                        return widgets
                    
                    # 如果widget可以聚焦且可见，添加到列表
                    if widget.isVisible() and widget.focusPolicy() != Qt.FocusPolicy.NoFocus:
                        widgets.append(widget)
                    
                    # 如果是容器，递归检查子widgets
                    layout = widget.layout()
                    if layout:
                        for i in range(layout.count()):
                            item = layout.itemAt(i)
                            if item:
                                # 获取子widget
                                child_widget = item.widget()
                                if child_widget:
                                    widgets.extend(get_focusable_widgets(child_widget))
                                # 如果有子layout，也递归检查
                                child_layout = item.layout()
                                if child_layout:
                                    for j in range(child_layout.count()):
                                        child_item = child_layout.itemAt(j)
                                        if child_item:
                                            grandchild_widget = child_item.widget()
                                            if grandchild_widget:
                                                widgets.extend(get_focusable_widgets(grandchild_widget))
                    return widgets
                
                layout = self.rightWidget.layout()
                if layout:
                    for i in range(layout.count()):
                        item = layout.itemAt(i)
                        if item:
                            widget = item.widget()
                            if widget:
                                unhidden_widgets.extend(get_focusable_widgets(widget))
                    
                # 去重并保持顺序
                seen = set()
                unique_widgets = []
                for widget in unhidden_widgets:
                    if widget not in seen and widget.isVisible() and widget.focusPolicy() != Qt.FocusPolicy.NoFocus:
                        seen.add(widget)
                        unique_widgets.append(widget)
                unhidden_widgets = unique_widgets
                
            # 检查是否有可聚焦的widgets
            if not unhidden_widgets:
                print("No focusable widgets found")
                return
                
            print(f"Found {len(unhidden_widgets)} focusable widgets")
            
            # 獲取當前焦點widget（如果有的話）
            current_focused = None
            if self.currentFocus < len(unhidden_widgets):
                current_focused = unhidden_widgets[self.currentFocus]
            
            # 檢查當前焦點是否在ComboBox上，且按的是上下鍵
            from PyQt6.QtWidgets import QComboBox
            # 檢查current_focused是否是ComboBox，或者是否有任何ComboBox在下拉狀態
            active_combobox = None
            if isinstance(current_focused, QComboBox):
                active_combobox = current_focused
            else:
                # 檢查是否有任何ComboBox的下拉菜單是打開的
                for widget in unhidden_widgets:
                    if isinstance(widget, QComboBox) and widget.view().isVisible():
                        active_combobox = widget
                        # 更新currentFocus指向這個ComboBox
                        if widget in unhidden_widgets:
                            self.currentFocus = unhidden_widgets.index(widget)
                        break
            
            if active_combobox and press in ["UP", "DOWN"]:
                # 如果當前焦點在ComboBox上且按的是上下鍵，直接操作ComboBox的下拉選單
                print(f"ComboBox focused, handling {press} key for option selection")
                # 如果下拉菜單未打開，先打開它
                if not active_combobox.view().isVisible():
                    active_combobox.showPopup()
                    # 等待下拉菜單打開
                    QTimer.singleShot(50, lambda: None)
                
                # 獲取當前索引並調整
                current_index = active_combobox.currentIndex()
                if press == "UP":
                    # 移動到上一個選項
                    if current_index > 0:
                        new_index = current_index - 1
                    else:
                        new_index = active_combobox.count() - 1
                else:  # DOWN
                    # 移動到下一個選項
                    if current_index < active_combobox.count() - 1:
                        new_index = current_index + 1
                    else:
                        new_index = 0
                
                # 設置新索引並觸發highlighted信號以朗讀
                active_combobox.setCurrentIndex(new_index)
                active_combobox.highlighted.emit(new_index)
                
                # 嘗試獲取當前選項的描述並朗讀
                try:
                    item_data = active_combobox.itemData(new_index, Qt.ItemDataRole.AccessibleTextRole)
                    if item_data:
                        speak(item_data)
                    else:
                        speak(active_combobox.itemText(new_index))
                except:
                    speak(active_combobox.itemText(new_index))
                
                return  # 不繼續切換焦點
            
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

            # 确保索引在有效范围内
            if self.currentFocus >= len(unhidden_widgets):
                self.currentFocus = 0
            if self.currentFocus < 0:
                self.currentFocus = len(unhidden_widgets) - 1
                
            target_widget = unhidden_widgets[self.currentFocus]
            print(f"Setting focus to widget: {target_widget}, index: {self.currentFocus}")
            target_widget.setFocus()
            try:
                intro = unhidden_widgets[self.currentFocus].text()
                if intro == "":
                    intro = unhidden_widgets[self.currentFocus].accessibleDescription()
            except:
                index = unhidden_widgets[self.currentFocus].currentIndex()
                intro = "Current Bot: " + unhidden_widgets[self.currentFocus].itemData(index, Qt.ItemDataRole.AccessibleTextRole)
                # intro = unhidden_widgets[self.currentFocus].currentText()
            
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
                    speak(Speak_template.analysis_help_message.value)
                else:
                    speak(Speak_template.setting_state_help_message.value)
                return
            case Bot_flow_status.board_init_status:
                speak(Speak_template.init_state_help_message.value)
                return
            case Bot_flow_status.select_status:
                if(Game_flow_status == Game_play_mode.computer_mode):
                    speak(Speak_template.select_computer_help_message.value)
                else:
                    speak(Speak_template.select_online_help_message.value)
            case Bot_flow_status.game_play_status:
                if self.input_mode == Input_mode.command_mode:
                    sentence = Speak_template.command_panel_help_message.value
                    # if self.game_play_mode == Game_play_mode.online_mode:
                    #     sentence = (
                    #         + Speak_template.command_panel_help_message.value
                    #     )

                    speak(sentence)
                elif self.input_mode == Input_mode.arrow_mode:
                    speak(
                        Speak_template.arrow_mode_help_message.value
                        + "or press control F for command mode"
                    )

    def voice_helper_menu(self):
        print("voice helper")
        match self.main_flow_status:
            case Bot_flow_status.setting_status:
                speak(Speak_template.setting_state_vinput_help_message.value)
                return
            case Bot_flow_status.board_init_status:
                speak(Speak_template.init_state_help_message.value)
                return
            case Bot_flow_status.select_status:
                if(Game_flow_status == Game_play_mode.computer_mode):
                    speak(Speak_template.select_computer_vinput_help_message.value)
                else:
                    speak(Speak_template.select_online_vinput_help_message.value)
            case Bot_flow_status.game_play_status:
                if self.input_mode == Input_mode.command_mode:
                    speak(Speak_template.command_panel_vinput_help_message.value)

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

        self.rightWidget.moveList.setText("Move List:\n" + self.moveListString)

    def refresh_move_list_from_board(self):
        """
        根據當前 chessBoard.board_object.move_stack 重新整理 move list
        並更新 opponentBox 顯示最後一步。主要用在悔棋後的同步更新。
        """
        if self.chessBoard is None:
            return

        # 重置計數狀態
        self.moveListString = ""
        self.moveList_line = 1
        self.moveList_element = 0

        moves = list(self.chessBoard.board_object.move_stack)
        last_uci = None

        for idx, move in enumerate(moves):
            try:
                uci = move.uci()
            except Exception:
                # 萬一 move 不是 chess.Move，嘗試轉成字串
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

        self.rightWidget.moveList.setText("Move List:\n" + self.moveListString)

        # 更新對手最後一步顯示
        if last_uci:
            self.rightWidget.opponentBox.setText(
                f"Opponent Last Move: {last_uci}"
            )
        else:
            self.rightWidget.opponentBox.setText("Opponent move: \n")

    def __init__(self, *args, **kwargs):

        self.settings = QSettings('ChessBot', 'config')
        print(self.settings.fileName())

        # 套用已儲存語言（要在建立 UI 前）
        try:
            saved_lang = self.settings.value("language", "en")
        except Exception:
            saved_lang = "en"
        set_language(str(saved_lang))


        print(f"rate: {speak_thread.rate}")
        print(f"volume: {speak_thread.volume}")
        
        global previous_sentence
        
        self.restoreConfig()

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
        self.whiteLoc = []
        self.blackLoc = []
        self.timeControl = ""
        # 在線對戰時間控制（多頁選單）狀態
        self.time_control_by_category = {}
        self.time_control_by_name = {}
        self.current_timecontrol_category = None
        self.current_timecontrol_options = []
        self.selected_time_control_name = None
        self.category_combobox = None
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
        shortcut_TAB.setContext(Qt.ShortcutContext.WindowShortcut)  # 在整个窗口范围内有效
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

        # 根據 time_control.txt 載入在線對戰時間控制配置
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
            voice_input_function=self.voice_input,
            fen_provider=self.get_current_fen,
        )
        # 偏好將焦點保持在聊天輸入欄（聊天機器人指令觸發時短暫生效）
        self._prefer_chatbot_focus = False

        def timeCallback(clocks):
            if not clocks == None:
                user_time = clocks[1].split(":")
                user = user_time[0] + " minutes " + user_time[1] + " seconds"

                opponent_time = clocks[0].split(":")
                opponent = (
                    opponent_time[0] + " minutes " + opponent_time[1] + " seconds"
                )
                speak(Speak_template.check_time_sentense.value.format(user, opponent))

        self.rightWidget.check_time.clicked.connect(
            partial(self.leftWidget.checkTime, timeCallback)
        )
        self.rightWidget.check_being_attacked.clicked.connect(
            self.macroView
        )
        # 目前棋局分析按鈕：僅在使用者按下時，才分析並朗讀當前局面
        try:
            self.rightWidget.currentGameAnalysisButton.clicked.connect(
                self.announce_game_situation
            )
        except Exception:
            pass
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

        # 悔棋按鈕：連到 undo_last_move
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
        
        self.mainWidget.setLayout(mainLayout)
        self.setCentralWidget(self.mainWidget)
        
        # 确保chatbot widget可见
        self.chatbotWidget.setVisible(True)
        self.chatbotWidget.show()
        self.chatbotWidget.setMinimumSize(300, 400)

        # 讓主視窗可由使用者拖曳調整大小，並依螢幕比例給初始尺寸
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

        # 保底尺寸，避免在小螢幕下太小
        init_w = max(init_w, 1280)
        init_h = max(init_h, 720)
        min_w = max(min_w, 1000)
        min_h = max(min_h, 600)

        self.setMinimumSize(min_w, min_h)
        self.resize(init_w, init_h)
        self.setMaximumSize(16777215, 16777215)

        # 强制更新布局
        mainLayout.update()
        mainLayout.activate()

        self.chessBoard = None
        self.userColor = None
        self.opponentColor = None
        self.online_game_started = False
        ##need to modify /Users/longlong/miniforge3/envs/fyp/lib/python3.12/site-packages/pyttsx3/drivers/nsss.py
        ## import objc and self.super
        # self.rightWidget.playWithComputerButton.setFocus()
        self.currentFocus = 0

        self.rightWidget.settingButton.clicked.connect(self.openSettingMenu)

        # Play with online player - 多頁時間控制選單
        # 第一頁：類別按鈕（Bullet / Blitz / Rapid / Daily）
        for category, btn in self.rightWidget.online_category_buttons.items():
            btn.clicked.connect(lambda checked=False, c=category: self.open_online_selection_page(c))

        # 第二頁：具體時間控制選項按鈕（依不同類別動態更新文字）
        for index, btn in enumerate(self.rightWidget.online_selection_buttons):
            btn.clicked.connect(lambda checked=False, idx=index: self.handle_online_selection_button(idx))

        # 返回上一頁（從選項頁回到類別頁）
        self.rightWidget.back_to_previous_page_button.clicked.connect(self.open_online_category_page)

        # 第二頁底部的 Start Game 按鈕
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
        self.rightWidget.play_button.clicked.connect(self.select_bot)

        self.rightWidget.combobox_coach.currentIndexChanged.connect(lambda index: self.bot_information(index, select=True))
        self.rightWidget.combobox_coach.highlighted.connect(self.bot_information)

        self.rightWidget.combobox_adaptive.currentIndexChanged.connect(lambda index: self.bot_information(index, select=True))
        self.rightWidget.combobox_adaptive.highlighted.connect(self.bot_information)

        self.rightWidget.combobox_beginner.currentIndexChanged.connect(lambda index: self.bot_information(index, select=True))
        self.rightWidget.combobox_beginner.highlighted.connect(self.bot_information)

        self.rightWidget.combobox_intermediate.currentIndexChanged.connect(lambda index: self.bot_information(index, select=True))
        self.rightWidget.combobox_intermediate.highlighted.connect(self.bot_information)

        self.rightWidget.combobox_advanced.currentIndexChanged.connect(lambda index: self.bot_information(index, select=True))
        self.rightWidget.combobox_advanced.highlighted.connect(self.bot_information)

        self.rightWidget.combobox_master.currentIndexChanged.connect(lambda index: self.bot_information(index, select=True))
        self.rightWidget.combobox_master.highlighted.connect(self.bot_information)

        self.rightWidget.combobox_athletes.currentIndexChanged.connect(lambda index: self.bot_information(index, select=True))
        self.rightWidget.combobox_athletes.highlighted.connect(self.bot_information)

        self.rightWidget.combobox_musicians.currentIndexChanged.connect(lambda index: self.bot_information(index, select=True))
        self.rightWidget.combobox_musicians.highlighted.connect(self.bot_information)

        self.rightWidget.combobox_creators.currentIndexChanged.connect(lambda index: self.bot_information(index, select=True))
        self.rightWidget.combobox_creators.highlighted.connect(self.bot_information)

        self.rightWidget.combobox_top_players.currentIndexChanged.connect(lambda index: self.bot_information(index, select=True))
        self.rightWidget.combobox_top_players.highlighted.connect(self.bot_information)

        self.rightWidget.combobox_personalities.currentIndexChanged.connect(lambda index: self.bot_information(index, select=True))
        self.rightWidget.combobox_personalities.highlighted.connect(self.bot_information)

        self.rightWidget.combobox_engine.currentIndexChanged.connect(lambda index: self.bot_information(index, select=True))
        self.rightWidget.combobox_engine.highlighted.connect(self.bot_information)

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
                speak("Restart Computer Game")

                def start_computer_new_game(result):
                    # 若當前頁面找不到 Rematch/New Game，退回電腦對戰頁重新開局
                    if not result:
                        self.playWithComputerHandler()

                    self.change_main_flow_status(Bot_flow_status.board_init_status)
                    QTimer.singleShot(800, self.getColor)
                    QTimer.singleShot(1000, self.initBoard)
                    QTimer.singleShot(1200, self.getBoard)
                    QTimer.singleShot(1400, lambda: self.change_main_flow_status(Bot_flow_status.game_play_status))

                self.leftWidget.chessWebView.page().runJavaScript(js_function.bot_new_game, start_computer_new_game)

            case Game_play_mode.online_mode:
                print("Starting a new game")
                speak("Starting a new game")

                # resign 後通常還在對局結果頁，先回到 online 建局頁再開新局
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
        speak("You have returned to home page")

## function to announce the pieces being attacked
    def macroView(self):
        # 防呆：未初始化棋盤時不執行，避免閃退
        if self.chessBoard is None or self.chessBoard.board_object is None:
            speak("No active game. Macro view is unavailable right now.")
            return
        if self.userColor is None:
            speak("Color is not assigned yet. Please start a game first.")
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
            # 準備聊天框文本
            if len(attacked_messages) == 0:
                chat_text = "Macro view: No pieces are under attack."
                speak("No pieces are under attack")
            else:
                max_items = 12
                shown = attacked_messages[:max_items]
                remainder = len(attacked_messages) - len(shown)
                chat_lines = [f"Macro view: {len(attacked_messages)} pieces are under attack."] + shown
                if remainder > 0:
                    chat_lines.append(f"And {remainder} more.")
                chat_text = "\n".join(chat_lines)

                # 語音：先總結，再逐條
                speak(f"Macro view: {len(attacked_messages)} pieces are under attack.")
                for line in shown:
                    speak(line)
                if remainder > 0:
                    speak(f"And {remainder} more.")

            # 寫入聊天窗口
            try:
                if hasattr(self, 'chatbotWidget') and hasattr(self.chatbotWidget, 'chat_display'):
                    self.chatbotWidget.chat_display.append(f"Chatbot: {chat_text}")
            except Exception as e2:
                print("Append macro view to chat failed:", e2)
        except Exception as e:
            print("Speak macro view failed:", e)

    def get_current_fen(self):
        """
        Provide the current board FEN for chatbot queries.
        """
        board_wrapper = getattr(self, "chessBoard", None)
        # 若當前已不在對局中（例如已認輸或對局結束），則不再提供 FEN
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
            return board_object.fen()
        except Exception as exc:
            print(f"Unable to get current FEN: {exc}")
            return None
    
    def announce_game_situation(self):
        """
        当检测到未结束的棋局时，自动分析当前局面并语音播报给用户
        """
        # 获取当前 FEN
        fen_value = self.get_current_fen()
        if not fen_value:
            print("无法获取当前 FEN，跳过局面分析")
            return
        
        # 获取用户颜色信息（如果还未设置，则根据当前回合推断）
        if hasattr(self, 'userColor') and self.userColor:
            user_color_text = "white" if self.userColor == "WHITE" else "black"
        else:
            # 如果 userColor 还未设置，根据当前回合推断
            user_color_text = "unknown"
        
        # 获取当前回合信息
        if hasattr(self, 'game_flow_status'):
            turn_text = "your turn" if self.game_flow_status == Game_flow_status.user_turn else "opponent's turn"
        else:
            turn_text = "unknown turn"
        
        # 构建 AI 分析提示
                    ##f"Here is the current chess position represented in FEN: {fen_value}. "
            ##f"The user is playing as {user_color_text} and it is currently {turn_text}. "
            ##"Give a short and concise description of the current situation, including: "
            ##"1. A brief evaluation of the position (who is better and why), "
            ##"2. which pieces are under attack, "
            ##"Please speak naturally and conversationally, as you are a chess assistant. "
            ##"Do not quote the FEN or repeat it back. Keep it concise and actionable."
        analysis_prompt = (

            "code:8888"
            f"current FEN: {fen_value}"
           f"user color: {user_color_text}"
            f"turn: {turn_text}"
        )
        
        print("Analyzing current game situation")
        speak("Analyzing current game situation")
        
        # 使用 chatbot 的 Gemini Worker 来分析局面
        if hasattr(self, 'chatbotWidget') and self.chatbotWidget:
            # 创建一个临时的 worker 来处理分析
            from ui.chatbot_window import OllamaWorker
            
            def on_analysis_complete(full_response: str):
                """分析完成后的回调：将結果送到右側 Chatbot 並朗讀"""
                print(f"棋局分析完成: {full_response}")
                chatbot_response = full_response
                try:
                    # 優先顯示在右側 Chatbot 對話框
                    if hasattr(self, "chatbotWidget") and self.chatbotWidget:
                        self.chatbotWidget.add_system_bot_message(chatbot_response)
                    else:
                        speak(chatbot_response)
                except Exception:
                    # 發生例外時至少仍然朗讀
                    speak(chatbot_response)
            
            def on_analysis_token(token: str):
                """流式输出时的回调（可选）"""
                pass
            
            # 创建并启动 Gemini Worker
            self._game_situation_worker = OllamaWorker(analysis_prompt)
            self._game_situation_worker.token_signal.connect(on_analysis_token)
            self._game_situation_worker.done_signal.connect(on_analysis_complete)
            self._game_situation_worker.start()
        else:
            print("Chatbot widget 未初始化，无法进行 AI 分析")
            speak("Unable to analyze game situation")

## display chatbot interface
    def chatbot(self):
            # 确保chatbot widget可见
            self.chatbotWidget.setVisible(True)
            self.chatbotWidget.show()
            # 聚焦到chatbot输入栏，让用户可以直接开始输入
            if hasattr(self.chatbotWidget, 'message_input'):
                self.chatbotWidget.message_input.setFocus()
                self.chatbotWidget.message_input.activateWindow()
                # 使用延时确保输入栏真正获得焦点（因为窗口可能需要一些时间来完成显示）
                QTimer.singleShot(100, lambda: self.chatbotWidget.message_input.setFocus())
            # speak("Hello! I am a Chat Bot. How can I help you today? Type in your question and I will answer immediately. You can type in how to use for help.")
    
    def handle_transcribed_text(self, text: str):
        """語音轉文字完成後的統一處理：顯示用戶內容 → 規則/動作優先 → 否則交給 Ollama"""
        if not text:
            return
        # 標記已開始處理（防止 checkAction 重複執行）
        voice_input_thread.processed_by_chatbot = True
        # 1) 右側顯示用戶內容
        self.chatbotWidget.add_user_bubble(text)
        # 2) 規則/動作優先（沿用 ChatbotWindow 的規則邏輯，會觸發 action_signal）
        result = self.chatbotWidget.get_bot_response(text.lower())

        delegated_message = None
        if isinstance(result, tuple):
            response, delegated_message = result
        else:
            response = result

        if response:
            # 顯示系統回覆文字（不走 Ollama）
            # 如果返回的是動作響應（如 "Executing move."），表示已觸發 action_signal
            self.chatbotWidget.add_system_bot_message(response)
            # 保持 processed_by_chatbot = True，阻止 checkAction 執行
            return

        # 3) 若無規則命中，或規則要求委派 LLM，才交給 Ollama
        # 即使沒有匹配規則，我們仍然標記為已處理，因為用戶可能只是想問問題
        # 而不是執行傳統的語音控制動作。這樣可以避免 checkAction 重複執行。
        self.chatbotWidget.start_ollama_for(delegated_message or text)

    # make action based on chatbot command (text input)
    def handle_chatbot_action(self, action: str):
        print(f"Received chatbot action: {action}")
        if not action:
            return
        normalized = action.strip().lower()

        # Direct chess operations from chatbot
        if normalized.startswith("move:"):
            move = normalized.split(":", 1)[1].strip()
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
            if self.game_play_mode == Game_play_mode.puzzle_mode:
                self.puzzle_movePiece(move)
            else:
                self.movePiece(move)
            # 走棋後短暫偏好聊天輸入欄焦點，避免被後續流程的 setFocus 奪走
            self._prefer_chatbot_focus = True
            self.focus_chatbot_input()
            QTimer.singleShot(700, self.focus_chatbot_input)
            QTimer.singleShot(1500, lambda: setattr(self, "_prefer_chatbot_focus", False))
            return

        if normalized.startswith("check:"):
            query = normalized.split(":", 1)[1].strip()
            if not query:
                return
            # Reuse existing handler by putting text into UI field
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
        if normalized == "start_computer_game":
            self.playWithComputerHandler()
            return
        if normalized == "start_player_game":
            self.playWithOtherButtonHandler()
            return
        if normalized == "get_board_state":
            self.getBoard()
            return
        if normalized == "home":
            self.returnHomePage()
            return
        if normalized == "puzzle":
            self.puzzleModeHandler()
            return

        # Resign current game
        if normalized == "resign":
            self.resign_handler()
            return

        if normalized == "open_settings":
            self.openSettingMenu()
            return

        # Macro View (piece attack overview)
        if normalized == "macro_view":
            try:
                if self.chessBoard is None:
                    speak("No active game. Please start or resume a game first.")
                    return
                print("Invoking macro view via chatbot...")
                QTimer.singleShot(200, self.macroView)
            except Exception as e:
                try:
                    speak("Macro view failed.")
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
                # 立即設一次
                self.chatbotWidget.message_input.setFocus()
                self.chatbotWidget.message_input.activateWindow()
                # 再用多次延遲回設，覆蓋後續可能的 setFocus()
                for delay in [50, 150, 300, 600]:
                    QTimer.singleShot(delay, lambda: self.chatbotWidget.message_input.setFocus())
        except:
            pass
    
## handle setting menu
    def openSettingMenu(self):
        global internal_speak_engine
        # 讀取目前語言
        try:
            current_lang = self.settings.value("language", "en")
        except Exception:
            current_lang = "en"

        menu = SettingMenu(
            rate=int((speak_thread.getRateValue() - 100) * 0.5),
            volume=int(speak_thread.getVolumeValue() * 100),
            engine=internal_speak_engine,
            language=str(current_lang),
            font_size=getattr(self, "_current_font_size", 22),
        )
        print(f"rate: {speak_thread.getRateValue()}, volume: {speak_thread.getVolumeValue()}")
        # menu.speech_rate_slider.setValue()
        # menu.speech_volume_slider.setValue()

        if menu.exec():
            self.speech_rate = menu.get_rate_value() * 2 + 100  # change to scale of interval 100 to 300
            self.speech_volume = menu.get_volume_value()
            internal_speak_engine = menu.get_engine_value()
            speak_thread.setRateValue(self.speech_rate)
            speak_thread.setVolumeValue(self.speech_volume)

            # 儲存並套用語言
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
            # 根據語言更新 TTS 所使用的 voice
            try:
                speak_thread.update_language(selected_lang)
            except Exception:
                pass

            # 套用並儲存字體大小
            selected_font_size = menu.get_font_size_value()
            self.apply_font_size(selected_font_size)
            try:
                self.settings.setValue("font_size", selected_font_size)
            except Exception:
                pass

    def undo_last_move(self):
        """
        悔棋：退回「自己和對手」共兩步，並嘗試在電腦對戰頁面發送 takeback 請求。
        """
        global speak
        if self.chessBoard is None or self.game_play_mode is None:
            speak(t("speak.game.undo.no_move"))
            return
        try:
            stack_len = len(self.chessBoard.board_object.move_stack)
            if stack_len == 0:
                speak(t("speak.game.undo.no_move"))
                return
            # 如果只有一手，就退一手；否則退兩手（對手與自己）
            pop_count = 1 if stack_len == 1 else 2
            for _ in range(pop_count):
                last_move = self.chessBoard.board_object.pop()
                print(f"Undo move: {last_move}")

            # 嘗試在棋盤右側控制列點擊「Undo last move」按鈕
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
                self.leftWidget.chessWebView.page().runJavaScript(jsCode)
            except Exception as e_js:
                print(f"undo_last_move JS failed: {e_js}")

            # 基於當前棋盤重新整理 move list 與對手最後一步顯示
            try:
                self.refresh_move_list_from_board()
            except Exception as e_refresh:
                print(f"refresh_move_list_from_board failed: {e_refresh}")

            # 重新從網頁取得棋子位置，更新 whitePieces / blackPieces
            try:
                QTimer.singleShot(
                    500,
                    lambda: self.leftWidget.chessWebView.page().runJavaScript(
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
            QTimer.singleShot(500, lambda: self.leftWidget.chessWebView.page().runJavaScript(js_function.getGameId, callback1))

        def callback1(gameId):
            print(gameId)
            self.leftWidget.chessWebView.loadFinished.connect(lambda: QTimer.singleShot(3000, lambda: self.leftWidget.chessWebView.page().runJavaScript(js_function.checkReviewLimited, callback2)))
            if(self.game_play_mode == Game_play_mode.computer_mode):
                self.leftWidget.chessWebView.load(QUrl(f"https://www.chess.com/analysis/game/computer/{gameId}"))
            else:
                self.leftWidget.chessWebView.load(QUrl(f"https://www.chess.com/analysis/game/live/{gameId}"))

        def callback2(ReviewLimited):
            print(f"Reivew Limited: {ReviewLimited}")
            self.leftWidget.chessWebView.loadFinished.disconnect()
            if(ReviewLimited):
                print("You have used your free Game Review for the day.")
                speak("You have used your free Game Review for the day.")
                self.shortcut_A.activated.connect(self.analysisModeHandler)
            else:
                # self.leftWidget.key_signal.connect(self.analysisAction)
                self.analysis_mode_switch(True)
                self.keyPressed_Signal.connect(self.analysisAction)
                self.leftWidget.chessWebView.page().runJavaScript(js_function.clickStartReview, callback3)
                self.change_game_mode(Game_play_mode.analysis_mode)

        def callback3(value):
            if(value == None):
                QTimer.singleShot(1000, lambda: self.leftWidget.chessWebView.page().runJavaScript(js_function.clickStartReview, callback3))
            else:
                callback4(value)

        def callback4(comment):
            QTimer.singleShot(300, lambda: self.leftWidget.chessWebView.page().runJavaScript(js_function.analysis_GetMoveLength, setMoveLength))
            self.leftWidget.chessWebView.setFocus()
            self.gameReviewMode_Reader(comment)

        def checkLogin(button):
            if(button != None):
                print("Please login for Game Review Function")
                speak("Please login for Game Review Function")
                return
            self.shortcut_A.activated.disconnect()
            self.bestExist = False
            self.analysisCount = 0
            self.keyPressed = None
            self.analysisBoard = ChessBoard()
            self.moveLength = -1
            self.best_pressed = False
            self.leftWidget.chessWebView.page().runJavaScript(js_function.clickGameReview, callback0)
        
        # if(self.game_flow_status != Game_flow_status.game_end):
        #     print("No finished game for analysis")
        #     speak("No finished game for analysis")
        #     return
        self.leftWidget.chessWebView.page().runJavaScript(js_function.checkLogin, checkLogin)
        


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
                self.leftWidget.chessWebView.page().runJavaScript(js_function.analysis_retry)
                self.analysisBoard.board_object.pop()
                self.best_pressed = False
            if(self.explain != None):
                self.rightWidget.analysisExplanation.setText("Explanation: \n" + self.explain)
            else:
                self.rightWidget.analysisExplanation.setText("Explanation: No content")
        else:
            if(self.keyPressed == Qt.Key.Key_Left):
                self.analysisBoard.board_object.pop()
            self.feedback = comment
            self.rightWidget.analysisCurrentMove.setText("Current Move: This is the beginning")

        print(self.analysisBoard.board_object)
        self.rightWidget.analysisComment.setText("Game Review Comment: \n" + self.feedback)
        print(self.feedback)
        speak(self.feedback)

    def gameReviewMode_Explainer(self):
        print(self.explain)
        speak(self.explain)

    def getReviewComment(self):
        self.leftWidget.chessWebView.page().runJavaScript(js_function.getReviewComment, self.gameReviewMode_Reader)

    def analysisAction(self, key):
        if(self.game_play_mode == Game_play_mode.analysis_mode):
            print(f"key: {key}")
            match key:
                case Qt.Key.Key_Left:
                    self.keyPressed = Qt.Key.Key_Left
                    if(self.analysisCount == 0):
                        speak("This is the beginning")
                    else:
                        self.analysisCount -= 1
                        QTimer.singleShot(300, self.getReviewComment)
                        
                case Qt.Key.Key_Right:
                    self.keyPressed = Qt.Key.Key_Right
                    if(self.analysisCount == self.moveLength):
                        speak("This the last move")
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
                        self.leftWidget.chessWebView.page().runJavaScript(js_function.analysis_GetBestMove)
                        self.poppedMove = self.analysisBoard.board_object.pop()
                        QTimer.singleShot(1000, self.getReviewComment)
                    else:
                        print("The current move is the best move")
                        speak("The current move is the best move")

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

        self.rightWidget.analysisCurrentMove.setText(("Current Move: \n" + result))
        return result
    
    def analysis_NextMove(self):
        if (self.cooldown == True):
            return
        self.cooldown = True
        self.cooldownTimer.start(500)
        self.leftWidget.chessWebView.page().runJavaScript(js_function.analysis_NextMove)
        QTimer.singleShot(100, lambda: self.keyPressed_Signal.emit(Qt.Key.Key_Right))

    def analysis_PreviousMove(self):
        if (self.cooldown == True):
            return
        self.cooldown = True
        self.cooldownTimer.start(500)
        self.leftWidget.chessWebView.page().runJavaScript(js_function.analysis_PreviousMove)
        QTimer.singleShot(100, lambda: self.keyPressed_Signal.emit(Qt.Key.Key_Left))

    def analysis_FirstMove(self):
        if (self.cooldown == True):
            return
        self.cooldown = True
        self.cooldownTimer.start(500)
        self.leftWidget.chessWebView.page().runJavaScript(js_function.analysis_FirstMove)
        QTimer.singleShot(100, lambda: self.keyPressed_Signal.emit(Qt.Key.Key_Up))

    # def analysis_LastMove(self):
    #     self.leftWidget.chessWebView.page().runJavaScript(js_function.analysis_LastMove)
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

    def voice_input(self):
        print("Ctrl S is pressed")
        # 如果正在處理音頻，只允許關閉語音輸入，不允許開啟新的錄音
        if voice_input_thread.is_processing:
            print("Audio is being processed, please wait...")
            speak("Audio is being processed, please wait...")
            return
        
        if not voice_input_thread.press_event.is_set():
            print("Voice Input activated. Listening...")
            speak("Voice Input activated. Listening...")
            voice_input_thread.press_event.set()
        else:
            voice_input_thread.press_event.clear()
            print("Voice input End")
            speak("Voice input end")

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
                if self.game_play_mode == Game_play_mode.puzzle_mode:
                    self.puzzle_movePiece(voice_input_thread.chess_move)
                else:
                    self.movePiece(voice_input_thread.chess_move)
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
        if(key in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_E, Qt.Key.Key_B)):
            self.keyPressed_Signal.emit(event.key())
    
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
        self.is_processing = False  # 標誌是否正在處理音頻
        self.processed_by_chatbot = False  # 標誌是否已被 chatbot 處理

        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = whisper.load_model("./small.en.pt", device=device)
        
        
        self.text_output = ""
        self.daemon = True
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = 1024
        self.frames = []
        self.chess_move = []
        self.start()
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK)

    def run(self):
        while True:
            self.press_event.wait()
            if self.press_event.is_set():
                self.record()

    def record(self):
        print("Voice Input function running")
        while self.press_event.is_set():
            data = self.stream.read(self.CHUNK)
            self.frames.append(data)
        if self.frames:
            print("Voice Input Ended")
            # 標記開始處理音頻
            self.is_processing = True
            try:
                with wave.open("./tmp.wav", 'wb') as wf:
                    wf.setnchannels(self.CHANNELS)
                    wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
                    wf.setframerate(self.RATE)
                    wf.writeframes(b''.join(self.frames))
                self.frames=[]
                print("Speech to Text performing...")
                self.text_output = self.model.transcribe("./tmp.wav", fp16=False)["text"].lower()
                print(f"Speech to Text finished! Output: {self.text_output}")
                # 重置處理標誌
                self.processed_by_chatbot = False
                # 將完整辨識文本發送出去（給聊天框與 ollama 使用）
                # 使用 Qt.CallType.QueuedConnection 確保信號處理完成後再執行 checkAction
                try:
                    # 直接調用處理函數來確保同步執行
                    if hasattr(window, 'handle_transcribed_text'):
                        window.handle_transcribed_text(self.text_output)
                    else:
                        self.transcribed_signal.emit(self.text_output)
                except Exception:
                    pass
                # 只有在 chatbot 沒有處理的情況下才調用 checkAction
                if not self.processed_by_chatbot:
                    self.checkAction()
            except Exception as e:
                print(f"Error processing audio: {e}")
            finally:
                # 確保處理完成後清除標誌
                self.is_processing = False
                self.frames = []
        else:
            self.frames = []
        # self.stream.stop_stream()
        # self.stream.close()
        # self.audio.terminate()

    def _fallback_to_ai(self):
        """語音指令未命中規則時，將原文轉交 AI 回覆。"""
        try:
            if hasattr(window, 'handle_transcribed_text'):
                self.processed_by_chatbot = True
                window.handle_transcribed_text(self.text_output)
                return
        except Exception as e:
            print(f"fallback to ai failed: {e}")

        # 最終保底：給使用者提示
        speak("我先把這個問題交給 AI，請稍候。")

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
                    # 非規則指令：轉交 AI 回覆
                    self._fallback_to_ai()
                case Game_play_mode.online_mode:
                    find = False
                    for item in timeControlDeterminant_Speak:
                        if (find == True):
                            break
                        for words in item.value:
                            if(words in self.text_output):
                                print(f"Time Control: {item.value[words]}")
                                self.action_signal.emit(item.value[words])
                                find = True
                                break
                    if(find == False):
                        # 非規則指令：轉交 AI 回覆
                        self._fallback_to_ai()
                case Game_play_mode.puzzle_mode:
                    # 非規則指令：轉交 AI 回覆
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
            # 非規則指令：轉交 AI 回覆
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
            speak("Invalid Input")

if __name__ == "__main__":
    global speak_thread
    global voice_input_thread
    global current_dir
    global previous_sentence
    previous_sentence = ""

    current_dir = os.path.dirname(os.path.realpath(__file__))

    # 在創建線程之前設置環境變數，確保 whisper 能找到 ffmpeg
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        ffmpeg_dir = os.path.join(os.path.dirname(sys.executable), 'ffmpeg', 'bin')
        my_env = os.environ
        my_env['PATH'] = f"{ffmpeg_dir}{os.pathsep}{my_env['PATH']}"
    else:
        ffmpeg_dir = os.path.join(current_dir, 'ffmpeg', 'bin')
        my_env = os.environ
        my_env['PATH'] = f"{ffmpeg_dir}{os.pathsep}{my_env['PATH']}"

    speak_thread = TTSThread()  #activate TTS module
    voice_input_thread = VoiceInput_Thread()  #activate S2T module

    # print(my_env)

    app = QApplication(sys.argv)

    font = QFont()
    font.setPointSize(22)
    app.setFont(font)
    app.setApplicationName("Chess Bot")

    window = MainWindow()


    icon = QIcon(os.path.join(current_dir, "Resource", "Logo", "chessBot_logo.png"))
    window.setWindowIcon(icon)

    # 確保窗口顯示
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

