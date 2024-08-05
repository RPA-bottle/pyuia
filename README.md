# pyuia

本项目是基于[Python-UIAutomation-for-Windows](https://github.com/yinkaisheng/Python-UIAutomation-for-Windows)（以下简称uiautomation）开发的，通过类似`xpath`风格的语言来实现自动化查找元素，实现windows软件的自动化。

这是我利用闲暇时间开发的，没有太多时间进行测试和维护，因此并不是所有`xpath`语法都支持。由于是对uiautomation的二次开发，原理是解析`xpath`语法，通过遍历元素来筛选符合要求的元素， 因此速度不像uiautomation那么快。


# 基本使用
以下是一个简单的例子，打开记事本，并写入文本。
```python
from pyuia import auto, desktop

# 查看目前运行的应用
print(desktop.children)
# 打开记事本
# subprocess.Popen('notepad.exe', shell=True)
# 获取记事本
app = desktop.wait_appear_by_xpath('./Window[@ClassName="Notepad"]')
screenWidth, screenHeight = auto.GetScreenSize()
app.MoveWindow(screenWidth // 4, screenHeight // 4, screenWidth // 2, screenHeight // 2)
app.SetActive()

# 打印记事本元素结构，着pyuia里面，使用xml的结构来展示元素的层级关系
app.print_tree()

# 获取并打印编辑窗口的元素节点
edit = app.find_by_xpath('//Edit')
edit.print_node()

# 写入文本
text = '''
Hello, world!
Welcome to pyuia!
'''
edit.SendKeys('{Ctrl}A{DELETE}', 0.2, 0)
edit.SendKeys('{Ctrl}{End}{Enter}下面开始演示{! 4}{ENTER}', 0.2, 0)
edit.SendKeys(text)
edit.SendKeys('[]{{}{}}\\|;:\'\",<.>/?{ENTER}', waitTime=0)

# 此外，pyuia还支持正则表达式，表达式字符串一定要加上`r`来避免转义。
app.find_by_xpath('//MenuItem[@Name="格式(O)"]').Click()
app.find_by_xpath(r'//MenuItem[re:match(@Name, "^字体.+")]').Click()
window_font = app.find_by_xpath('//Window[@Name="字体"]')
window_font.find_by_xpath('//Button[@Name="确定"]').Click()

app.GetWindowPattern().Close()
if auto.WaitForDisappear(app, 3):
    print("Notepad closed")
else:
    print("Notepad still exists after 3 seconds")
    app.find_by_xpath(r'//Button[re:match(@Name, "不保存.+")]').Click()
```
更多的例子，请查看`demos`文件夹下的文件。


# TODO
- 通过python来遍历windows元素来查找符合条件的目标元素，这个过程很慢，未来要进行重大升级，直接将`xpath`表达式转换为`uiautomation`的python代码，通过减少遍历来提速。  
- 目前`xpath`的表达式是通过`re`来解析的，精力有限，我只支持了最常用的`xpath`语法，对于轴语法，仅支持`self`、`ancestor`、`preceding-sibling`、`following-sibling`、`parent`、`descendant`和`child`。如果你知道可以直接解析`xpath`的python库，请联系我，十分感谢。


