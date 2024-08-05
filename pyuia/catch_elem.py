import os, sys
from os.path import dirname, join
sys.path.append(join(dirname(dirname(dirname(dirname(__file__)))), 'site-packages'))
print(join(dirname(dirname(dirname(__file__))), 'site-packages'))
from element import UIAElement
import uiautomation as auto
# import time
import sys
import subprocess
import psutil


def main():
    while 1:
        ctrl = auto.ControlFromCursor()
        if ctrl:
            elem = UIAElement(ctrl)
            elem_string = elem.get_node()
            print(f'\r{elem_string}{" "*(100-len(elem_string))}', end='')


def xpath():
    ctrl = auto.ControlFromCursor()
    if ctrl:
        elem = UIAElement(ctrl)
        xpath = elem.get_path()
        auto.Logger.WriteLine(f'\nroot ctrl: {UIAElement(elem.GetTopLevelControl())}', auto.ConsoleColor.Green)
        auto.Logger.WriteLine(f'xpath: {xpath}', auto.ConsoleColor.Green)
        auto.SetClipboardText(xpath)


def HotKeyFunc(stopEvent, argv):
    args = [sys.executable, __file__] + argv
    cmd = ' '.join('"{}"'.format(arg) for arg in args)
    p = subprocess.Popen(cmd)
    while True:
        if p.poll() is not None:
            break
        if stopEvent.is_set():
            childProcesses = [pro for pro in psutil.process_iter() if pro.ppid == p.pid or pro.pid == p.pid]
            for pro in childProcesses:
                p.kill()
            break
        stopEvent.wait(0.5)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--main', action='store_true', help='exec main')
    parser.add_argument('--xpath', action='store_true', help='exec xpath')
    args = parser.parse_args()
    if args.main:
        main()
    elif args.xpath:
        xpath()
    else:
        auto.RunByHotKey(
            {
                (auto.ModifierKey.Control, auto.Keys.VK_1): lambda event: HotKeyFunc(event, ['--main']),
                (auto.ModifierKey.Control, auto.Keys.VK_2): lambda event: HotKeyFunc(event, ['--xpath'])
            },
            (auto.ModifierKey.Control, auto.Keys.VK_3)
        )
