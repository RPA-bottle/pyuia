import uiautomation as auto
import re
from xml.sax.saxutils import escape
import subprocess
from datetime import datetime
import os
from PIL import Image
try:
    from IPython.display import display
except:
    pass
import time


'''
TODO 总览
- 在notebook提供一个html格式的节点展示，点击可以展开节点，并看到具体信息。
'''

class UIAElement:
    attrs_map = {
        'Name': 'Name',
        'AutomationId': 'AutomationId',
        'ClassName': 'ClassName',
    }


    def __init__(self, ctrl=None):
        self.ctrl = ctrl
        #NOTE - 请确保uiautomation.Control是存在的，否则会因为无法
        #       设置属性而等待很长时间甚至报错。
        for attr in dir(ctrl):
            if not attr.startswith('_'):
                setattr(self, attr, getattr(ctrl, attr))

 
    def __repr__(self):
        if self.ctrl is None:
            return 'None'
        control_type = self.ControlTypeName[:-7]
        attrs_dct = {key: getattr(self, value) for key, value in self.attrs_map.items()}
        code = ''.join([f' {key}="{escape(attr)}"'  for key, attr in attrs_dct.items() if attr != ''])
        code = f'<{control_type}{code}>'
        if len(self.children) == 0:
            return code.replace('>', ' />')
        else:
            return code.replace('>', f'>...</{control_type}>')


    def __bool__(self):
        return self.ctrl is not None
    
        
    def get_tree(self, indent=0):
        control_type = self.ControlTypeName[:-7]
        attrs_dct = {key: getattr(self, value) for key, value in self.attrs_map.items()}
        code = ''.join([f' {key}="{escape(attr)}"'  for key, attr in attrs_dct.items() if attr != ''])
        code = f'{"    "*indent}<{control_type}{code}>\n'
        
        children = self.children
        if len(children) == 0:
            return code.replace('>', ' />')
        else:
            code += ''.join([child.get_tree(indent+1) for child in children])
            code += f'{"    "*indent}</{control_type}>\n'
            return code
            
    def print_tree(self, fpath=None):
        code = self.get_tree()
        print(code)
        if fpath:
            with open(fpath, 'w') as f:
                f.write(code)

    def get_node(self):
        return self.__str__()

    def print_node(self):
        print(self)

    @property
    def root(self):
        return self.__class__(self.GetTopLevelControl())

    @property
    def ctrl_type(self):
        return self.ControlTypeName[:-7]

    @property
    def ancestors(self):
        if self.IsTopLevel():
            return []
        elems = [self.parent]
        while 1:
            elems.append(elems[-1].parent)
            if elems[-1].IsTopLevel():
                return elems

    @property
    def parent(self):
        return self.__class__(self.GetParentControl())

    @property
    def children(self):
        return [self.__class__(ctrl) for ctrl in self.GetChildren()]
        
    @property
    def siblings(self):
        return [self.__class__(ctrl) for ctrl in self.GetParentControl().GetChildren()]


    @property
    def following_sibling(self):
        ctrl = self.GetNextSiblingControl()
        if ctrl is None:
            return
        else:
            return self.__class__(ctrl)


    @property
    def first_child(self):
        ctrl = self.GetFirstChildControl()
        if ctrl is None:
            return
        else:
            return self.__class__(ctrl)


    @property
    def following_siblings(self):
        ctrl = self.ctrl
        elems = []
        while 1:
            ctrl = ctrl.GetNextSiblingControl()
            if ctrl == None:
                return elems
            elems.append(self.__class__(ctrl))


    @property
    def preceding_siblings(self):
        return self.siblings[:-len(self.following_siblings)-1]


    def get_path(self):
        path = ''
        if self.IsTopLevel():
            return '.'
        elem = self
        while 1:            
            ctrl_type = elem.ctrl_type
            elems = [item for item in elem.preceding_siblings if item.ctrl_type==ctrl_type]
            _next = elem.following_sibling
            index = len(elems) + 1
            path = f'{ctrl_type}/{path}' if index == 1 and _next is None else f'{ctrl_type}[{index}]/{path}'
            elem = elem.parent
            if elem.parent.parent.ctrl is None:
                return f'./{path[:-1]}'

            
            
    def iter_self(self, compare, status=None, found_index=None, is_find_all=False):
        if compare(self):
            yield self
        else:
            return
        

    def iter_descendants(self, compare, status=None, found_index=None, is_find_all=False):
        is_init, _found_index, child = True, 0, self
        while True:
            if is_init:
                child = child.first_child
                is_init = False
            else:
                child = child.following_sibling
            if child is None:
                return
            if compare(child):
                _found_index += 1
                if found_index is None or found_index == _found_index:
                    yield child
                    if not is_find_all:
                        status['is_finished'] = True
                        return
                    elif found_index is not None:
                        return
            yield from child.iter_descendants(compare, status, found_index, is_find_all)
            if not is_find_all and status['is_finished']:
                return
            

    def iter_children(self, compare, status=None, found_index=None, is_find_all=False):
        is_init, _found_index = True, 0
        while True:
            if is_init:
                child = self.first_child 
                is_init = False
            else:
                child = child.following_sibling
            if child is None:
                return
            
            if compare(child):
                _found_index += 1
                if found_index is None:
                    yield child
                    if not is_find_all:
                        return
                elif found_index == _found_index:
                    yield child
                    return 
                

    def iter_parent(self, compare=None, status=None, found_index=None, is_find_all=False):
        yield self.parent


    def iter_ancestors(self, compare, status=None, found_index=None, is_find_all=False):        
        #NOTE - ancestor 通过parent来查找祖先元素，因此顺序是从当前元素的父元素开始往上查找的
        #       与lxml的xpath不一致。
        ancestor, _found_index = self, 0
        while True:
            ancestor = ancestor.parent
            if not ancestor:
                return
            if compare(ancestor):
                _found_index += 1
                if found_index is None or found_index == _found_index:
                    yield ancestor
                    if not is_find_all or found_index:
                        return
            if ancestor.IsTopLevel():
                return
            

    def iter_preceding_siblings(self, compare, status=None, found_index=None, is_find_all=False):
        prec, _found_index = self, 0
        while 1:
            prec = self.__class__(prec.GetPreviousSiblingControl())
            if prec:
                if compare(prec):
                    _found_index += 1
                    if found_index is None or found_index == _found_index:
                        yield prec
                        if not is_find_all or found_index:
                            return
            else:
                return


    def iter_following_siblings(self, compare, status=None, found_index=None, is_find_all=False):
        _next, _found_index = self, 0
        while True:
            _next = self.__class__(_next.GetNextSiblingControl())
            if _next:
                if compare(_next):
                    _found_index += 1
                    if found_index is None or found_index == _found_index:
                        yield _next
                        if not is_find_all or found_index:
                            return
            else:
                return


    def find_by_xpath(self, xpath):
        return Xpath().find_by_xpath(self, xpath)
    

    def find_all_by_xpath(self, xpath):
        return Xpath().find_all_by_xpath(self, xpath)


    def send(self, message, interval=0.01, waitTime=0.5, clear=True, simulation=False):
        '''文本框输入'''
        pattern = self.GetLegacyIAccessiblePattern()
        if clear:
            # 清空当前文本
            self.SendKeys('{Ctrl}a{Back}')
            if simulation:
                self.SendKeys(message, interval, waitTime)
                time.sleep(0.5)
                if pattern.Value != message:
                    pattern.SetValue(message)
                    time.sleep(0.1)
            else:
                pattern.SetValue(message)
            if pattern.Value != message:
                raise RuntimeError('Text box cannot be entered')          
        else:
            _message = pattern.Value + message
            if simulation:
                self.SendKeys(message, interval, waitTime)
                time.sleep(0.5)
                if pattern.Value != _message:
                    pattern.SetValue(_message)
                    time.sleep(0.1)
            else:
                    pattern.SetValue(_message)
            if pattern.Value != _message:
                raise RuntimeError('Text box cannot be entered')

 
    def clear(self):
        '''文本框输入'''
        pattern = self.GetLegacyIAccessiblePattern()
        # 清空当前文本
        self.SendKeys('{Ctrl}a{Back}')
        if pattern.Value != '':
            pattern.SetValue('')
        if pattern.Value != '':
            raise RuntimeError('Text box cannot be entered')          

 


    def screenshot(self, path=None, notebook=True, show=True):
        if path is None:
            now = datetime.now()
            path = now.strftime('./tmp/%Y%m%d_%H%M%S_%f.png')
            if not os.path.exists('./tmp'):
                os.mkdir('./tmp')
        self.CaptureToImage(path)
        if notebook and show:
            display(Image.open(path))
        elif show:
            Image.open(path).show()



    def wait_disappear_by_xpath(self, xpath, timeout=5, interval=0.1):
        t0, dt = time.time(), 0
        while dt < timeout:
            elem = self.find_by_xpath(xpath)
            if elem:
                elem.Disappears(timeout-dt, interval)
                return True
            time.sleep(interval)
            dt = time.time() - t0
        return False

    def wait_appear_by_xpath(self, xpath, timeout=5, interval=0.1):
        t0, dt = time.time(), 0
        while dt < timeout:
            elem = self.find_by_xpath(xpath)
            if elem:
                return elem
            time.sleep(interval)
            dt = time.time() - t0
        return self.__class__(None)
            

class Xpath:
    pt_var = r'[^/\[\]\(\)@=\s]+?'
    cpt_axis = re.compile(r'^/{1,2}(\w*-?\w*)::(.*)')
    cpt_ctrl_type = re.compile(r'^/{0,2}\s*([\w\*]+)\s*\[?')
    cpt_condition = re.compile(r'\[([^\[\]]*@[^\[\]]*)\]')
    cpt_index = re.compile(r'\[\s*(\d+)\s*\]')
    # cpt_pair = re.compile(rf'\s*@\s*({pt_var})\s*=\s*[\'\"]([^/\[\]@=\s]+?)[\'\"]\s*')
    cpt_pair = re.compile(rf'\s*@\s*({pt_var})\s*=\s*(?<!\\)[\'\"](.*?)(?<!\\)[\'\"]\s*')
    # cpt_pair_ns = re.compile(rf'\s*({pt_var}):({pt_var})\s*\(\s*@\s*({pt_var})'
    #                         r'\s*,\s*[\'\"](.*)[\'\"]\s*\)\s*')
    cpt_pair_ns = re.compile(rf'\s*([^\s]+?):([^\s]*)\s*\(\s*@\s*([^\s]*)'
                            r'\s*,\s*(?<!\\)[\'\"](.*?)(?<!\\)[\'\"]\s*\)\s*')
    
    axis_map = {
        'ancestor': 'iter_ancestors',
        'preceding-sibling': 'iter_preceding_siblings',
        'following-sibling': 'iter_following_siblings',
        'parent': 'iter_parent',
        'descendant': 'iter_descendants',
        'child': 'iter_children'
    }

    def __init__(self) -> None:
        self.selectors = {}


    def get_exprs(self, xpath):
        '''
        预处理xpath表达式。包括清洗和拆分xpath表达式两部分。
        以下表达式会进行替换
        ---------------------------------------
        | Original | Replacement              |
        ---------------------------------------
        | /..      | /parent::*               |
        | //.      | /descendant::*           |
        | //..     | /descendant::*/parent::* |
        ---------------------------------------
        然后将一个完整的表达式拆分成若干个表达式。
        '''
        # 当有3个以上的`/`或者`.`，都会被判定为非法表达式
        if '///' in xpath or '...' in xpath\
            or xpath.endswith('/'):
            raise SyntaxError('Invalid expression')
        
        xpath = xpath.strip()
        if re.match(r'^[^/\.]', xpath):
            xpath = './'+xpath
        elif xpath.startswith('..'):
            xpath = xpath.replace('..', './..', 1)
        from_elem = 'self' if xpath.startswith('.') else 'root'

        # 删除斜杠前后多余的空格
        xpath = re.sub(r'\s*/\s*', '/', xpath)
        # 将符号化的轴转换为字符形式的轴
        replacement = {
            '/..': '/parent::*',
            '//.': '/descendant::*',
            '//..': '/descendant::*/parent::*'
        }
        exprs = [replacement.get(item, item) for item in re.findall(r'/{1,2}[^/]+', xpath) if item != '/.']
        xpath = ''.join(exprs).replace('//', '/descendant::')
        #FIXME - 如果元素的属性里面包含了斜杆？
        #   会解析失败，弹出语法错误提示。
        exprs = [item if re.match(r'/[^\[]*::', item) else '/child::'+item[1:] for item in re.findall(r'/{1,2}[^/]+', xpath)]
        return from_elem, exprs

    def get_axis(self, expr):
        axis, expr = self.cpt_axis.findall(expr)[0]
        if axis not in self.axis_map:
            raise SyntaxError(f'Invalid axis: {axis}')
        return axis, expr

    def get_ctrl_type(self, expr):
        if not self.cpt_ctrl_type.match(expr):
            raise SyntaxError('Invalid expression')
        ctrl_type = self.cpt_ctrl_type.findall(expr)[0]
        if ctrl_type == '*':
            ctrl_type = None
        elif ctrl_type.isalpha():
            ctrl_type = ctrl_type+'Control'
        else:
            raise SyntaxError('Invalid expression')
        return ctrl_type

    def get_conditions(self, expr):
        conditions = []
        for string in self.cpt_condition.findall(expr):
            code = self.cpt_pair.sub(' $ ', string)
            for k, v in self.cpt_pair.findall(string):
                code = code.replace('$', f'c.{k}=="{v}"', 1)
            code = self.cpt_pair_ns.sub(' $ ', code)

            for module, func, k, v in self.cpt_pair_ns.findall(string):
                code = code.replace('$', f'{module}.{func}("{v}", c.{k})', 1)
            conditions.append(code)
        return conditions


    def get_index(self, expr):
        index = None
        for index in self.cpt_index.findall(expr):
            index = int(index)
            if index < 1:
                raise ValueError('Element index must be greater than 0')
        return index


    def get_selector(self, expr):
        axis, expr = self.get_axis(expr)
        ctrl_type = self.get_ctrl_type(expr)
        conditions = [] if ctrl_type is None else [f' c.ControlTypeName=="{ctrl_type}" ']
        conditions.extend(self.get_conditions(expr))
        conditions = 'and'.join(conditions).strip()
        index = self.get_index(expr)
        if axis == 'parent' and (conditions or index is not None):
            raise SyntaxError('Invalid Expression')
        if conditions:
            compare = f'lambda c: {conditions}'
            try:
                compare = eval(compare)
            except:
                raise SyntaxError('Invalid expression:', expr)
        else:
            compare = lambda c: True
        return {'axis': self.axis_map[axis], 'compare': compare, 'found_index': index}

    
    def get_selectors(self, xpath):
        self.selectors = dict()
        from_elem, exprs = self.get_exprs(xpath)
        for i, expr in enumerate(exprs):
            self.selectors[i+1] = self.get_selector(expr)
        return from_elem, self.selectors
    
    
    def _find(self, elem, status=None, idx_selector=0, selectors=None):
        idx_selector += 1    
        is_find_all = status['is_find_all'] if idx_selector == len(selectors) else True

        iterator = getattr(elem, selectors[idx_selector]['axis'])(
            compare=selectors[idx_selector]['compare'],
            found_index=selectors[idx_selector]['found_index'],
            status=status,
            is_find_all=is_find_all,
        )
        while True:
            try:
                elem = next(iterator)
                if idx_selector == len(selectors):
                    yield elem
                    if not status['is_find_all']:
                        status['is_finished'] = True
                else:
                    yield from self._find(elem, status, idx_selector, selectors)
                    if status['is_finished']:
                        return
            except StopIteration:
                return
    

    def find_by_xpath(self, elem, xpath):
        status = {'is_find_all': False, 'is_finished': False}
        from_elem, selectors = self.get_selectors(xpath)
        elem = elem if from_elem == 'self' else elem.root
        res = list(self._find(elem, status, 0, selectors))
        return res[0] if res else None


    def find_all_by_xpath(self, elem, xpath):
        status = {'is_find_all': True, 'is_finished': False}
        from_elem, selectors = self.get_selectors(xpath)
        elem = elem if from_elem == 'self' else elem.root
        return list(self._find(elem, status, 0, selectors))
        


if __name__ == '__main__':
    app = auto.WindowControl(searchDepth=1, ClassName='Notepad', RegexName='.* - 记事本')
    if not app.Exists(0.2):
        subprocess.Popen('notepad.exe', shell=True)
    uapp = UIAElement(app)

    uapp.find_by_xpath('//MenuItem[@Name="格式(O)"]').Click()
    elem = uapp.find_by_xpath('//MenuItem[re:match(Name, "^字体.+")]')


    uelem = Xpath().find_by_xpath(uapp, '//Edit//Button[@Name="下一行"]')
    print(uelem)

    uelem = Xpath().find_by_xpath(uapp, r'//MenuItem[re:match(@Name, "文件\(F\)")]')
    print(uelem)

    uelem = Xpath().find_by_xpath(uapp, '//MenuItem[@Name="文件(F)"]')
    print(uelem)

    uelem = Xpath().find_by_xpath(uapp, '//Edit//Button[2]')
    print(uelem)

    uelems = Xpath().find_all_by_xpath(uapp, '//Edit//Button[2]')
    print(uelems)

    uelem = uapp.find_by_xpath('//Edit//Button[@Name="下一行"]')
    print(uelem)

    uelems = uapp.find_all_by_xpath('//Edit//Button[2]')
    print(uelems)

    uelem = Xpath().find_by_xpath(uapp, '//Edit//Button[@Name="下一行"]')
    print(uelem.find_by_xpath('/..'))

