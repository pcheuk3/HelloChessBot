# ui/left_widget.py
import os
from PyQt6.QtWidgets import QVBoxLayout, QWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from PyQt6.QtCore import QUrl
current_dir = os.path.dirname(os.path.realpath(__file__))


class LeftWidget(QWidget):
    """
    This class respresent the left widget.
    It contains chess.com web view and invisible grids that assigned after board detection
    """

    def __init__(self):
        super().__init__()

        self.chessWebView = QWebEngineView()

        # profile to store the user account detail
        self.profile = QWebEngineProfile("storage", self.chessWebView)
        self.profile.setPersistentStoragePath(
            os.path.join(current_dir, "Tmp", "chess_com_account")
        )

        web_page = QWebEnginePage(self.profile, self.chessWebView)
        self.chessWebView.setPage(web_page)
        self.chessWebView.load(QUrl("https://www.chess.com"))

        self.chessWebView.setMinimumSize(1000, 550)
        # self.chessWebView.setFixedSize(1000, 550)

        vlayout = QVBoxLayout()
        vlayout.addWidget(self.chessWebView)
        vlayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(vlayout)

        # an 8x8 grid holder (will be replaced by QLabel widgets once board is detected)
        self.grids = [[0 for x in range(8)] for y in range(8)]

    # crawl remaining time (runs JS on the chess.com page and returns clocks via callback)
    def checkTime(self, callBack):
        jsCode = """
            function checkTime() {
                const selectors = [
                    '.clock-time-monospace',
                    '.clock-component .clock-time',
                    '[data-cy="clock-time"]',
                    '[class*="clock-time"]'
                ];

                let clocks = [];
                for (const selector of selectors) {
                    clocks = Array.from(document.querySelectorAll(selector)).filter(el => {
                        const txt = (el.textContent || '').trim();
                        return txt.length > 0;
                    });
                    if (clocks.length >= 2) {
                        break;
                    }
                }

                if (clocks.length < 2) {
                    return null;
                }

                return [
                    (clocks[0].textContent || '').trim(),
                    (clocks[1].textContent || '').trim()
                ];
            }
            checkTime();
            """
        return self.chessWebView.page().runJavaScript(jsCode, callBack)
