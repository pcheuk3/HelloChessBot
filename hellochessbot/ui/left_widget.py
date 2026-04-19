# ui/left_widget.py
import os
import sys
from pathlib import Path
import Components.js_function as js_function
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QSizePolicy
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from PyQt6.QtCore import QUrl


def _get_runtime_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


runtime_dir = _get_runtime_base_dir()


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
            str(runtime_dir / "Tmp" / "chess_com_account")
        )

        web_page = QWebEnginePage(self.profile, self.chessWebView)
        self.chessWebView.setPage(web_page)
        self.chessWebView.load(QUrl("https://www.chess.com"))

        # base (design) size used to compute proportional zoom factor
        self.base_width = 1000
        self.base_height = 550

        # allow the webview to expand with the layout
        self.chessWebView.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.chessWebView.setMinimumSize(self.base_width // 2, self.base_height // 2)

        vlayout = QVBoxLayout()
        vlayout.addWidget(self.chessWebView)
        vlayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(vlayout)

        # an 8x8 grid holder (will be replaced by QLabel widgets once board is detected)
        self.grids = [[0 for x in range(8)] for y in range(8)]

    def resizeEvent(self, event):
        """Scale the web page proportionally based on the widget size.

        Uses the base design size to compute a zoom factor and applies it
        to the QWebEngineView so the page scales by percentage when the
        window is resized.
        """
        super().resizeEvent(event)

        try:
            w = self.chessWebView.width()
            h = self.chessWebView.height()
            # compute a uniform scale preserving aspect ratio
            scale_w = w / float(self.base_width) if self.base_width else 1.0
            scale_h = h / float(self.base_height) if self.base_height else 1.0
            scale = min(scale_w, scale_h)
            # keep zoom factor in a reasonable range
            if scale <= 0:
                scale = 0.1
            # apply zoom factor to the web page
            self.chessWebView.setZoomFactor(scale)
            # notify main window to reposition overlay grids if available
            try:
                from PyQt6.QtCore import QTimer

                QTimer.singleShot(50, lambda: getattr(self.window(), 'reposition_grids', lambda: None)())
            except Exception:
                pass

            # refresh board base coordinates from the page so physical click mapping stays accurate
            try:
                def _cb(coor):
                    try:
                        win = self.window()
                        if win and hasattr(win, 'update_board_base'):
                            win.update_board_base(coor)
                    except Exception:
                        pass

                self.chessWebView.page().runJavaScript(js_function.getBoard, _cb)
            except Exception:
                pass
        except Exception:
            # be tolerant to any unexpected errors during resize
            pass

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
