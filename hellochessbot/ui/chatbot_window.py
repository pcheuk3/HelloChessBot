"""
ChatBot Window UI Component
Backend: local FastAPI `/chat` which calls Replicate.
"""

import html
import re
import requests
import os
import sys
import uuid
from pathlib import Path
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
from PyQt6.QtGui import QShortcut, QKeySequence, QTextCursor

from Utils.enum_helper import (
    chatbot_response,
)
from Utils.i18n import t


CHAT_API_URL = "https://hellochessbot.uk/chat"
CHAT_API_TOKEN = "hddkqg3kiuddglwasbiajoijks"  # API key of fastapi server


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


def _get_app_base_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


class ChatbotWindow(QWidget):
    """ChatBot UI"""
    action_signal = pyqtSignal(str)

    def __init__(
        self,
        speak_function=None,
        tts_thread=None,
        voice_input_function=None,
        voice_input_press_function=None,
        voice_input_release_function=None,
        fen_provider=None,
    ):
        super().__init__()
        self.session_id = str(uuid.uuid4())
        self.setWindowFlags(Qt.WindowType.Widget)
        self.setMinimumSize(300, 400)
        self.speak = speak_function
        self.tts_thread = tts_thread
        self.chat_history: list[dict] = []
        self._last_user_payload: str = ""
        self._bot_response_start: int | None = None
        self.voice_input_function = voice_input_function
        self.voice_input_press_function = voice_input_press_function
        self.voice_input_release_function = voice_input_release_function
        self.fen_provider = fen_provider

        layout = QVBoxLayout(self)
        self.isInputArea = True

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setAcceptRichText(True)
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
        if self.voice_input_press_function:
            self.voice_input_button.pressed.connect(self.voice_input_press_function)
        if self.voice_input_release_function:
            self.voice_input_button.released.connect(self.voice_input_release_function)
        input_layout.addWidget(self.voice_input_button)

        self.update_voice_button_mode("toggle")

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

        welcome_html = self._build_bot_bubble(t("chat.welcome"))
        self._append_html_line(welcome_html)
        self.message_input.setFocus()

        self.current_focus_index = 1  # Start with message_input

        tab = QShortcut(QKeySequence("tab"), self)
        tab.setContext(Qt.ShortcutContext.WidgetShortcut)
        tab.activated.connect(self.tabHandler)

    def update_voice_button_mode(self, mode: str):
        normalized = "toggle" if str(mode).lower() == "toggle" else "hold"
        self.voice_trigger_mode = normalized
        desc_key = f"settings.voice_button.desc.{normalized}"
        tooltip_key = f"settings.voice_button.tooltip.{normalized}"
        self.voice_input_button.setAccessibleDescription(t(desc_key))
        self.voice_input_button.setToolTip(t(tooltip_key))

    def retranslate_ui(self):
        self.update_voice_button_mode(getattr(self, "voice_trigger_mode", "toggle"))
        self.message_input.setAccessibleDescription(t("chat.message_input.desc"))
        self.send_button.setText(t("chat.send_button.text"))
        self.send_button.setAccessibleDescription(t("chat.send_button.desc"))

    def send_message(self):
        user_message = self.message_input.text().strip()
        if not user_message:
            return

        if self.speak:
            self.speak(t("speak.chat.user_input", message=user_message))

        # user message bubble
        self._append_html_line(self._build_user_bubble(user_message))

        # move cursor to the end of the chat display
        self.chat_display.moveCursor(QtGui.QTextCursor.MoveOperation.End)

        result = self.get_bot_response(user_message)
        delegated_message = None

        if isinstance(result, tuple):
            response, delegated_message = result
        else:
            response = result

        if response:
            self._append_html_line(self._build_bot_bubble(response))
            self.chat_display.ensureCursorVisible()
            if self.speak:
                self.speak(response)
            self.message_input.clear()
            return

        question_text = delegated_message or user_message
        self._pending_question = question_text

        # request FEN sync
        try:
            self._request_fen_sync()
        except Exception:
            pass
        QTimer.singleShot(350, self._start_pending_worker)

        self.message_input.clear()

    def update_bot_response(self, token: str):
        # keep signal interface; actual display in finish_bot_response once, avoid overwriting old message
        _ = token
        self.chat_display.ensureCursorVisible()

    def finish_bot_response(self, full_payload: dict):
        reply_text = str(full_payload.get("reply") or "").strip()
        intent = str(full_payload.get("intent") or "").strip()
        action = full_payload.get("action")
        move_uci = full_payload.get("move_uci")
        move_san = full_payload.get("move_san")
        candidate_move_uci = full_payload.get("candidate_move_uci")
        candidate_move_san = full_payload.get("candidate_move_san")
        candidate_move_raw = full_payload.get("candidate_move_raw")

        if self._last_user_payload:
            self.chat_history.append({"role": "user", "content": self._last_user_payload})
            if reply_text:
                self.chat_history.append({"role": "assistant", "content": reply_text})
            if len(self.chat_history) > 10:
                self.chat_history = self.chat_history[-10:]

        if self.speak and reply_text:
            self.speak(reply_text)
        if reply_text:
            self._replace_pending_bot_text_with_html(self._build_bot_bubble(reply_text))
        else:
            self._replace_pending_bot_text_with_html(self._build_bot_bubble("(no reply)"))

        action_payload = None
        if action:
            action_payload = f"{action}"
        elif intent:
            action_payload = f"{intent}"

        move_payload = None
        for mv in (move_uci, move_san, candidate_move_uci, candidate_move_san, candidate_move_raw):
            if mv:
                move_payload = str(mv).strip()
                break

        if action_payload:
            if action_payload == "move_piece" and move_payload:
                self.action_signal.emit(f"move:{move_payload}")
            else:
                self.action_signal.emit(action_payload)

    def add_user_bubble(self, message_text: str):
        if not message_text:
            return
        self._append_html_line(self._build_user_bubble(message_text))
        self.chat_display.ensureCursorVisible()

    def add_system_bot_message(self, message_text: str):
        if not message_text:
            return
        self._append_html_line(self._build_bot_bubble(message_text))
        self.chat_display.ensureCursorVisible()
        if self.speak:
            self.speak(message_text)

    def start_replicate_for(self, message_text: str):
        if not message_text:
            return

        self.chat_display.moveCursor(QtGui.QTextCursor.MoveOperation.End)

        question_text = message_text
        self._pending_question = question_text

        # request FEN sync
        try:
            self._request_fen_sync()
        except Exception:
            pass
        QTimer.singleShot(350, self._start_pending_worker)

    def submit_external_message(self, message_text: str):
        if not message_text:
            return
        if self.speak:
            self.speak(t("speak.chat.user_input", message=message_text))
        self.add_user_bubble(message_text)
        self.start_replicate_for(message_text)

    def _build_user_bubble(self, message_text: str) -> str:
        return (
            '<div style="text-align: right; margin: 0;">'
            '<span style="background: #F5C731; color: black; border-radius: 16px 4px 16px 16px; padding: 10px 16px; display: inline-block; max-width: 70%;">'
            f'{t("chat.user_label")} :'
            '<div style="text-align: left; margin: 0;">'
            '<span style="background: #F5C731; color: black; border-radius: 16px 4px 16px 16px; padding: 10px 16px; display: inline-block; max-width: 70%;">'
            f'{self._format_rich_text(message_text)}'
            '</div>'
        )

    def _build_bot_bubble(self, message_text: str) -> str:
        return (
            '<div style="text-align: left; margin: 0;">'
            '<span style="background: #00008B; color: white; border-radius: 16px 16px 16px 4px; padding: 10px 16px; display: inline-block; max-width: 70%;">'
            f'{t("chat.bot_label")} :'
            '<div style="text-align: left; margin: 0;">'
            '<span style="background: #00008B; color: white; border-radius: 16px 16px 16px 4px; padding: 10px 16px; display: inline-block; max-width: 70%;">'
            f'{self._format_rich_text(message_text)}'
            
            '</div>'
        )

    def _append_html_line(self, html_text: str):
        if not html_text:
            return
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
        cursor.insertHtml(html_text)
        # insert two line breaks so there is one full blank line between messages
        cursor.insertHtml("<br/><br/>")

    def _format_rich_text(self, text: str) -> str:
        if not text:
            return ""

        formatted = html.escape(text)
        formatted = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", formatted)
        formatted = re.sub(r"__(.+?)__", r"<span style=\"background-color: #FFFF00;\">\1</span>", formatted)
        formatted = re.sub(r"~~(.+?)~~", r"<s>\1</s>", formatted)
        formatted = re.sub(r"\*(.+?)\*", r"<em>\1</em>", formatted)

        allowed_tags = {
            "b",
            "strong",
            "i",
            "em",
            "u",
            "span",
            "br",
            "ul",
            "ol",
            "li",
            "h1",
            "h2",
            "h3",
            "p",
            "small",
            "big",
            "sup",
            "sub",
        }

        def _restore_tag(match):
            closing, tag, attrs = match.groups()
            if tag.lower() in allowed_tags:
                return f"<{closing}{tag}{attrs}>"
            return match.group(0)

        formatted = re.sub(r"&lt;(/?)(\w+)([^&]*)&gt;", _restore_tag, formatted)
        formatted = formatted.replace("\n", "<br/>")
        return formatted

    def _replace_pending_bot_text(self, full_response: str):
        cursor = self.chat_display.textCursor()
        if self._bot_response_start is None:
            cursor.insertHtml(self._format_rich_text(full_response))
            # ensure one blank line after replaced bot text
            cursor.insertHtml("<br/><br/>")
            self.chat_display.moveCursor(QtGui.QTextCursor.MoveOperation.End)
            return

        end_pos = cursor.position()
        cursor.setPosition(self._bot_response_start)
        cursor.setPosition(end_pos, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertHtml(self._format_rich_text(full_response))
        # ensure one blank line after replaced bot text
        cursor.insertHtml("<br/><br/>")
        self.chat_display.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        self._bot_response_start = None

    def _replace_pending_bot_text_with_html(self, html_content: str):
        cursor = self.chat_display.textCursor()
        if self._bot_response_start is None:
            cursor.insertHtml(html_content)
            # ensure one blank line after replaced bot HTML
            cursor.insertHtml("<br/><br/>")
            self.chat_display.moveCursor(QtGui.QTextCursor.MoveOperation.End)
            return

        end_pos = cursor.position()
        cursor.setPosition(self._bot_response_start)
        cursor.setPosition(end_pos, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertHtml(html_content)
        # ensure one blank line after replaced bot HTML
        cursor.insertHtml("<br/><br/>")
        self.chat_display.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        self._bot_response_start = None

    def _fetch_user_color(self):
        if not self.fen_provider:
            return None
        try:
            return self.fen_provider("user_color")
        except Exception:
            return None

    def _fetch_current_fen(self):
        if not self.fen_provider:
            return None
        try:
            return self.fen_provider("fen")
        except Exception as exc:
            print(f"Failed to retrieve FEN: {exc}")
            return None

    def _fetch_latest_web_fen(self):
        if not self.fen_provider:
            return None
        try:
            return self.fen_provider("fen_latest")
        except Exception:
            return None

    def _request_fen_sync(self):
        if not self.fen_provider:
            return None
        try:
            return self.fen_provider("fen_sync_request")
        except Exception:
            return None

    def _refresh_fen_after_sync(self):
        """after sync, try to catch FEN, and update the ongoing chat request"""
        try:
            latest_fen = self._fetch_current_fen()
        except Exception:
            latest_fen = None
        if not latest_fen:
            return
        # if waiting for reply, and worker exists, then update with latest FEN
        try:
            if hasattr(self, "worker") and self.worker and getattr(self.worker, "fen", None) is None:
                self.worker.fen = latest_fen
        except Exception:
            pass

    def _start_pending_worker(self):
        question_text = getattr(self, "_pending_question", None)
        if not question_text:
            return

        # wait for latest FEN after web sync (avoid sending old position)
        attempts = int(getattr(self, "_pending_fen_attempts", 0))
        current_fen = self._fetch_latest_web_fen() or self._fetch_current_fen()
        if current_fen is None and attempts < 4:
            self._pending_fen_attempts = attempts + 1
            QTimer.singleShot(300, self._start_pending_worker)
            return

        # even if no FEN is available, still send (avoid message stuck)
        self._pending_fen_attempts = 0
        current_user_color = self._fetch_user_color()
        self._last_user_payload = question_text

        self.worker = replicateWorker(
            message=question_text,
            fen=current_fen,
            user_color=current_user_color,
            history=list(self.chat_history),
            session_id=self.session_id,
        )
        self.worker.token_signal.connect(self.update_bot_response)
        self.worker.done_signal.connect(self.finish_bot_response)
        self.worker.start()
        self._pending_question = None

    def get_bot_response(self, _message: str) -> str:

        return None

    def play_button_sound(self):
        print("Playing button sound")
        if self.tts_thread:
            sound_path = str(_get_app_base_dir() / 'Components' / 'Button.wav')
            print(f"Sound path: {sound_path}")
            self.tts_thread.play_sound(sound_path)

    def tabHandler(self):
        self.current_focus_index = (self.current_focus_index + 1) % len(self.chatbotLayout)
        widget = self.chatbotLayout[self.current_focus_index]
        widget.setFocus()
        # Play button sound if it's a button
        if isinstance(widget, QPushButton):
            self.play_button_sound()
        intro = widget.accessibleDescription() or ""
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


class replicateWorker(QThread):
    token_signal = pyqtSignal(str)
    done_signal = pyqtSignal(dict)

    def __init__(
        self,
        message: str,
        fen: str | None = None,
        user_color: str | None = None,
        model: str | None = None,
        history: list[dict] | None = None,
        session_id: str | None = None,
    ):
        super().__init__()
        self.message = message
        self.fen = fen
        self.user_color = user_color
        self.history = history or []
        self.session_id = session_id or "default"

    def run(self):
        try:
            headers = {
                "Authorization": f"Bearer {CHAT_API_TOKEN}",
                "Content-Type": "application/json",
            }

            payload = {
                "message": self.message,
                "fen": self.fen,
                "user_color": self.user_color,
                "level": "beginner",
                "depth": 16,
                "multipv": 3,
                "session_id": self.session_id,
                "in_game": bool(self.fen),
            }

            response = requests.post(
                CHAT_API_URL,
                json=payload,
                headers=headers,
                timeout=120,
            )

            if response.status_code != 200:
                self.done_signal.emit({
                    "reply": "server is closed, please try it later",
                    "intent": "unknown",
                    "action": None,
                })
                return

            try:
                data = response.json()
            except Exception as e:
                self.done_signal.emit({
                    "reply": f"Chat API returned non-JSON response: {e}",
                    "intent": "unknown",
                    "action": None,
                })
                return

            reply = str(data.get("reply") or "").strip()

            if reply:
                self.token_signal.emit(reply)

            self.done_signal.emit(data)

        except Exception:
            self.done_signal.emit({
                "reply": "server is closed, please try it later",
                "intent": "unknown",
                "action": None,
            })
