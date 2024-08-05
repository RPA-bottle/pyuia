from .element import UIAElement
import uiautomation as auto


def get_desktop():
    return UIAElement(auto.GetRootControl())
