#!python3
# -*- coding: utf-8 -*-
import os
import sys
import time
import subprocess
import ctypes

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # not required after 'pip install uiautomation'
from pyuia import auto, desktop

text = """The uiautomation module

This module is for UIAutomation on Windows(Windows XP with SP3, Windows Vista and Windows 7/8/8.1/10).
It supports UIAutomation for the applications which implmented IUIAutomation, such as MFC, Windows Form, WPF, Modern UI(Metro UI), Qt and Firefox.

Run 'automation.py -h' for help.

uiautomation is shared under the Apache Licene 2.0.
This means that the code can be freely copied and distributed, and costs nothing to use.

代码原理介绍: http://www.cnblogs.com/Yinkaisheng/p/3444132.html
"""


def test_notepad():
    # 打开notepad
    subprocess.Popen('notepad.exe', shell=True)
    # 等待元素出现
    app = desktop.wait_appear_by_xpath('./Window[@ClassName="Notepad"]')
    screenWidth, screenHeight = auto.GetScreenSize()
    app.MoveWindow(screenWidth // 4, screenHeight // 4, screenWidth // 2, screenHeight // 2)
    app.SetActive()
    edit = app.find_by_xpath('//Edit')
    edit.SendKeys('{Ctrl}A{DELETE}', 0.2, 0)
    edit.SendKeys('{Ctrl}{End}{Enter}下面开始演示{! 4}{ENTER}', 0.2, 0)
    edit.SendKeys(text)
    edit.SendKeys('[]{{}{}}\\|;:\'\",<.>/?{ENTER}', waitTime=0)

    app.find_by_xpath('//MenuItem[@Name="格式(O)"]').Click()
    app.find_by_xpath(r'//MenuItem[re:match(@Name, "^字体.+")]').Click()

    app.find_by_xpath('//List/ListItem[@Name="微软雅黑"]')
    window_font = app.find_by_xpath('//Window[@Name="字体"]')
    elem = app.find_by_xpath('//List/ListItem[@Name="微软雅黑"]')
    window_font = app.find_by_xpath('//Window[@Name="字体"]')
    elem = window_font.find_by_xpath('//List/ListItem[@Name="微软雅黑"]')
    if elem:
        elem.GetScrollItemPattern().ScrollIntoView()
        elem.Click()

    combo = window_font.find_by_xpath('//ComboBox[@AutomationId="1140"]')
    combo.Click()
    combo.find_by_xpath('./List/ListItem[@Name="中文 GB2312"]').Click()
    valuePt = combo.GetValuePattern()
    if valuePt:
        print('current selection:', valuePt.Value)
    selectPt = combo.GetSelectionPattern()
    if selectPt:
        print('current selection:', selectPt.GetSelection())
    window_font.find_by_xpath('//Button[@Name="确定"]').Click()

    app.GetWindowPattern().Close()
    if auto.WaitForDisappear(app, 3):
        print("Notepad closed")
    else:
        print("Notepad still exists after 3 seconds")
        app.find_by_xpath(r'//Button[re:match(@Name, "不保存.+")]').Click()


if __name__ == "__main__":
    test_notepad()
