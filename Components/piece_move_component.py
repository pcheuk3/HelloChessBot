from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication
import time
import pyautogui

##simulate mouse click and move to make piece move on web view
def widgetDragDrop(targetWidget, destWidget):
    QTest.mouseMove(targetWidget)
    time.sleep(0.3)
    pyautogui.leftClick()
    time.sleep(0.3)
    QTest.mouseMove(destWidget)
    time.sleep(0.3)
    pyautogui.leftClick()
    return True


##simulate mouse click to select promotion
def widgetClick(targetWidget):
    QTest.mouseMove(targetWidget)
    QApplication.processEvents()
    pyautogui.leftClick()
    QApplication.processEvents()
    return True

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