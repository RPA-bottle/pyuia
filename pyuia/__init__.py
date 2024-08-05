from .element import UIAElement
from .utils import get_desktop
import uiautomation as auto


__all__ = ['element', 'auto', 'desktop']
desktop = get_desktop()
# desktop = UIAElement(auto.GetRootControl())

