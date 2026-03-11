"""
ChatBot Window UI Component
Backend: local FastAPI `/chat` which calls Replicate.
"""

import re
import requests
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QPushButton,
    QLineEdit,
    QHBoxLayout,
    QTextEdit,
)
from PyQt6 import QtGui
from PyQt6.QtCore import pyqtSignal, Qt, QThread, QTimer
from PyQt6.QtGui import QShortcut, QKeySequence

from Utils.enum_helper import (
    timeControlDeterminant_Type,
    chatbot_response,
)
from Utils.i18n import t


CHAT_API_URL = "https://www.hellochessbot.uk/chat"
CHAT_API_TOKEN = "hddkqg3kiuddglwasbiajoijks"  # 改成你的 APP_API_KEY


SAN_MOVE_PATTERN = re.compile(
    r"""
    ^
    (?:
        (?:[kqrbn](?:[a-h]|[1-8]|[a-h][1-8])?x?[a-h][1-8])
        |
        (?:[a-h]x)?[a-h][1-8](?:=[qrbn])?
        |
        (?:oo|ooo)
    )
    [+#]?$
    """,
    re.VERBOSE,
)


class ChatbotWindow(QWidget):
    """ChatBot UI"""
    action_signal = pyqtSignal(str)

    def __init__(self, speak_function=None, voice_input_function=None, fen_provider=None):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.Widget)
        self.setMinimumSize(300, 400)
        self.speak = speak_function
        self.chat_history: list[dict] = []
        self._last_user_payload: str = ""
        self.voice_input_function = voice_input_function
        self.fen_provider = fen_provider

        layout = QVBoxLayout(self)
        self.isInputArea = True

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)
        self.chat_display.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        self.chat_display.ensureCursorVisible()

        input_layout = QHBoxLayout()

        self.voice_input_button = QPushButton("🎤")
        self.voice_input_button.setAccessibleDescription(t("chat.voice_button.desc"))
        self.voice_input_button.setToolTip(t("chat.voice_button.tooltip"))
        self.voice_input_button.setFixedSize(40, 30)
        if self.voice_input_function:
            self.voice_input_button.clicked.connect(self.voice_input_function)
        input_layout.addWidget(self.voice_input_button)

        self.message_input = QLineEdit()
        self.message_input.setAccessibleDescription(t("chat.message_input.desc"))
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input)

        self.send_button = QPushButton(t("chat.send_button.text"))
        self.send_button.setAccessibleDescription(t("chat.send_button.desc"))
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setAutoDefault(True)
        input_layout.addWidget(self.send_button)

        layout.addLayout(input_layout)

        self.chatbotLayout = [
            self.voice_input_button,
            self.message_input,
            self.send_button,
        ]

        self.chat_display.append(t("chat.welcome"))
        self.message_input.setFocus()

        tab = QShortcut(QKeySequence("tab"), self)
        tab.setContext(Qt.ShortcutContext.WidgetShortcut)
        tab.activated.connect(self.tabHandler)

    def retranslate_ui(self):
        self.voice_input_button.setAccessibleDescription(t("chat.voice_button.desc"))
        self.voice_input_button.setToolTip(t("chat.voice_button.tooltip"))
        self.message_input.setAccessibleDescription(t("chat.message_input.desc"))
        self.send_button.setText(t("chat.send_button.text"))
        self.send_button.setAccessibleDescription(t("chat.send_button.desc"))

    def send_message(self):
        user_message = self.message_input.text().strip()
        if not user_message:
            return

        self.chat_display.append(t("chat.you_prefix", message=user_message))
        self.chat_display.append(t("chat.bot_prefix"))
        self.chat_display.moveCursor(QtGui.QTextCursor.MoveOperation.End)

        result = self.get_bot_response(user_message)
        delegated_message = None

        if isinstance(result, tuple):
            response, delegated_message = result
        else:
            response = result

        if response:
            self.chat_display.insertPlainText(response)
            self.chat_display.ensureCursorVisible()
            if self.speak:
                self.speak(response)
            self.message_input.clear()
            return

        question_text = delegated_message or user_message
        self._last_user_payload = question_text
        current_fen = self._fetch_current_fen()

        self.worker = OllamaWorker(
            message=question_text,
            fen=current_fen,
            history=list(self.chat_history),
        )
        self.worker.token_signal.connect(self.update_bot_response)
        self.worker.done_signal.connect(self.finish_bot_response)
        self.worker.start()

        self.message_input.clear()

    def update_bot_response(self, token: str):
        self.chat_display.insertPlainText(token)
        self.chat_display.ensureCursorVisible()

    def finish_bot_response(self, full_response: str):
        if self._last_user_payload:
            self.chat_history.append({"role": "user", "content": self._last_user_payload})
            if full_response:
                self.chat_history.append({"role": "assistant", "content": full_response})
            if len(self.chat_history) > 10:
                self.chat_history = self.chat_history[-10:]

        if self.speak:
            self.speak(full_response)

    def add_user_bubble(self, message_text: str):
        if not message_text:
            return
        self.chat_display.append(t("chat.you_prefix", message=message_text))
        self.chat_display.ensureCursorVisible()

    def add_system_bot_message(self, message_text: str):
        if not message_text:
            return
        self.chat_display.append(t("chat.bot_line", message=message_text))
        self.chat_display.ensureCursorVisible()
        if self.speak:
            self.speak(message_text)

    def start_ollama_for(self, message_text: str):
        if not message_text:
            return

        self.chat_display.append("Chatbot: ")
        self.chat_display.moveCursor(QtGui.QTextCursor.MoveOperation.End)

        question_text = message_text
        self._last_user_payload = question_text
        current_fen = self._fetch_current_fen()

        self.worker = OllamaWorker(
            message=question_text,
            fen=current_fen,
            history=list(self.chat_history),
        )
        self.worker.token_signal.connect(self.update_bot_response)
        self.worker.done_signal.connect(self.finish_bot_response)
        self.worker.start()

    def submit_external_message(self, message_text: str):
        if not message_text:
            return
        self.add_user_bubble(message_text)
        self.start_ollama_for(message_text)

    def _fetch_user_color(self):
        try:
            color = getattr(self, "user_color", None)
        except Exception:
            color = None
        return color

    def _fetch_current_fen(self):
        if not self.fen_provider:
            return None
        try:
            return self.fen_provider()
        except Exception as exc:
            print(f"Failed to retrieve FEN: {exc}")
            return None

    def get_bot_response(self, message: str) -> str:
        """
        Rule-based + backend fallback
        """
        uci_pattern = re.compile(r"^[a-h][1-8][a-h][1-8][qrbn]?$")
        check_pattern = re.compile(r"^(?:check|pos|position)\s+(.+)$")
        resign_pattern = re.compile(r"\b(resign|i\s+resign|give\s+up)\b")
        macro_pattern = re.compile(r"\b(macro\s*view|macroview|macro|attack\s*map)\b")
        setting_pattern = re.compile(r"\b(settings?|preferences|open\s+settings?)\b")

        normalized_message = re.sub(r"[^\sa-z0-9]", "", message.lower()).strip()

        fen_command_variants = {
            "fen",
            "current fen",
            "what is the fen",
            "what is fen",
            "whats the fen",
            "what's the fen",
            "show fen",
            "get fen",
            "tell me the fen",
            "fen please",
        }

        situation_variants = {
            "situation",
            "current situation",
            "what is the situation",
            "whats the situation",
            "what's the situation",
        }

        if normalized_message in fen_command_variants:
            fen_value = self._fetch_current_fen()
            if fen_value:
                return f"Current FEN: {fen_value}"
            return "can't get current FEN, please ensure the game is active."

        if normalized_message in situation_variants:
            fen_value = self._fetch_current_fen()
            if fen_value:
                return (
                    None,
                    "Please describe the current position clearly: who is better, the key ideas, and the practical plan for the side to move."
                )
            return "can't get current FEN, please ensure the game is active."

        move_candidate = self._normalize_move_candidate(message)
        if move_candidate and uci_pattern.match(move_candidate):
            self.action_signal.emit(f"move:{move_candidate}")
            return "Executing move."

        if move_candidate and SAN_MOVE_PATTERN.match(move_candidate):
            self.action_signal.emit(f"move:{move_candidate}")
            return "Executing move."

        m = check_pattern.match(message)
        if m:
            query = m.group(1).strip()
            self.action_signal.emit(f"check:{query}")
            return "Checking position."

        if resign_pattern.search(message.lower()):
            self.action_signal.emit("resign")
            return "Resigning."

        if macro_pattern.search(message.lower()):
            self.action_signal.emit("macro_view")
            return "Opening macro view."

        if setting_pattern.search(message.lower()):
            QTimer.singleShot(0, lambda: self.action_signal.emit("open_settings"))
            return "Opening settings."

        for item in chatbot_response:
            for words in item.value:
                if re.search(rf"\b{re.escape(words)}\b", message.lower()):
                    action_name = item.name.lower()
                    print(f"Triggering chatbot action: {action_name}")
                    self.action_signal.emit(action_name)
                    return item.value[words]

        for item in timeControlDeterminant_Type:
            for words in item.value:
                if re.search(rf"\b{re.escape(words)}\b", message.lower()):
                    tc_value = item.value[words]
                    print(f"Time Control Detected: {tc_value}")
                    self.action_signal.emit(f"vc:timecontrol:{tc_value}")
                    self.hide()
                    return f"Starting an online player Game with {tc_value}"

        return None

    def tabHandler(self):
        self.isInputArea = not self.isInputArea
        idx = int(self.isInputArea)
        self.chatbotLayout[idx].setFocus()
        intro = self.chatbotLayout[idx].accessibleDescription() or ""
        if self.speak:
            self.speak(intro)

    def _normalize_move_candidate(self, raw: str) -> str:
        if not raw:
            return ""
        cleaned = re.sub(r"\s+", "", raw.lower())
        cleaned = cleaned.replace("null", "")
        cleaned = cleaned.replace("to", "")
        cleaned = cleaned.replace("-", "")
        cleaned = cleaned.replace("0", "o")
        return cleaned


class OllamaWorker(QThread):
    token_signal = pyqtSignal(str)
    done_signal = pyqtSignal(str)

    def __init__(
        self,
        message: str,
        fen: str | None = None,
        model: str | None = None,
        history: list[dict] | None = None,
    ):
        super().__init__()
        self.message = message
        self.fen = fen
        self.history = history or []

    def run(self):
        try:
            headers = {
                "Authorization": f"Bearer {CHAT_API_TOKEN}",
                "Content-Type": "application/json",
            }

            payload = {
                "message": self.message,
                "fen": self.fen,
                "level": "beginner",
                "depth": 16,
                "multipv": 3,
            }

            response = requests.post(
                CHAT_API_URL,
                json=payload,
                headers=headers,
                timeout=120,
            )

            if response.status_code != 200:
                self.done_signal.emit(
                    f"Chat API HTTP error: {response.status_code} - {response.text}"
                )
                return

            try:
                data = response.json()
            except Exception as e:
                self.done_signal.emit(f"Chat API returned non-JSON response: {e}")
                return

            reply = str(data.get("reply") or "").strip()

            if reply:
                self.token_signal.emit(reply)
                self.done_signal.emit(reply)
            else:
                self.done_signal.emit("")

        except Exception as e:
            self.done_signal.emit(f"Chat API request failed: {e}")