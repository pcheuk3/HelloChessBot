from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QPoint
import time
import pyautogui


def _scale_global_point(widget, point: QPoint) -> QPoint:
    """Convert Qt global (logical) coordinates to screen (physical) coordinates."""
    ratio = 1.0
    try:
        screen = widget.screen() or QApplication.primaryScreen()
        if screen is not None:
            ratio = float(screen.devicePixelRatio())
    except Exception:
        ratio = 1.0
    return QPoint(int(point.x() * ratio), int(point.y() * ratio))


##simulate mouse click and move to make piece move on web view
def widgetDragDrop(targetWidget, destWidget):
    try:
        # move to center of target widget in global coordinates
        p = targetWidget.mapToGlobal(targetWidget.rect().center())
        p = _scale_global_point(targetWidget, p)
        pyautogui.moveTo(p.x(), p.y())
        time.sleep(0.15)
        pyautogui.click()
        time.sleep(0.15)
        p2 = destWidget.mapToGlobal(destWidget.rect().center())
        p2 = _scale_global_point(destWidget, p2)
        pyautogui.moveTo(p2.x(), p2.y())
        time.sleep(0.15)
        pyautogui.click()
        return True
    except Exception:
        return False
    return True


##simulate mouse click to select promotion
def widgetClick(targetWidget):
    try:
        p = targetWidget.mapToGlobal(targetWidget.rect().center())
        p = _scale_global_point(targetWidget, p)
        pyautogui.moveTo(p.x(), p.y())
        QApplication.processEvents()
        pyautogui.click()
        QApplication.processEvents()
        return True
    except Exception:
        return False

def moveRight(x, y, x_scale, interval):
    pyautogui.moveTo(x, y)
    pyautogui.mouseDown(button="left")
    time.sleep(0.3)
    pyautogui.moveTo(x + (interval * x_scale), y)
    pyautogui.mouseUp(button="left")

def moveLeft(x, y, x_scale, interval):
    pyautogui.moveTo(x, y)
    pyautogui.mouseDown(button="left")
    time.sleep(0.3)
    pyautogui.moveTo(x - (interval * x_scale), y)
    pyautogui.mouseUp(button="left")

def moveUp(x, y, y_scale, interval):
    pyautogui.moveTo(x, y)
    pyautogui.mouseDown(button="left")
    time.sleep(0.3)
    pyautogui.moveTo(x, y - (interval * y_scale))
    pyautogui.mouseUp(button="left")

def moveDown(x, y, y_scale, interval):
    pyautogui.moveTo(x, y)
    pyautogui.mouseDown(button="left")
    time.sleep(0.3)
    pyautogui.moveTo(x, y + (interval * y_scale))
    pyautogui.mouseUp(button="left")

def moveTopRight(x, y, x_scale, y_scale, interval):
    pyautogui.moveTo(x, y)
    pyautogui.mouseDown(button="left")
    time.sleep(0.3)
    pyautogui.moveTo(x + (interval*x_scale), y - (interval * y_scale))
    pyautogui.mouseUp(button="left")

def moveBottomRight(x, y, x_scale, y_scale, interval):
    pyautogui.moveTo(x, y)
    pyautogui.mouseDown(button="left")
    time.sleep(0.3)
    pyautogui.moveTo(x + (interval * x_scale), y + (interval * y_scale))
    pyautogui.mouseUp(button="left")

def moveTopLeft(x, y, x_scale, y_scale, interval):
    pyautogui.moveTo(x, y)
    pyautogui.mouseDown(button="left")
    time.sleep(0.3)
    pyautogui.moveTo(x - (interval * x_scale), y - (interval * y_scale))
    pyautogui.mouseUp(button="left")

def moveBottomLeft(x, y, x_scale, y_scale, interval):
    pyautogui.moveTo(x, y)
    pyautogui.mouseDown(button="left")
    time.sleep(0.3)
    pyautogui.moveTo(x - (interval * x_scale), y + (interval * y_scale))
    pyautogui.mouseUp(button="left")