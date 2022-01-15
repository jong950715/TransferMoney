from decimal import Decimal
from tkinter import ttk
import tkinter as tk

from selfLib.MyList import MyList
from work.Enums import TransferDir

MAX_TABLE_LINES = 10
PREPARING_WORD = '준비중'
PREPARING_DATA = [[PREPARING_WORD]]


class MyViewWindow:
    def __init__(self, window):
        self.window = window
        self.widgets = dict()
        self._initTreeView()

    def _initTreeView(self):
        _cols = ['ticker', 'krw/usdt', 'krw/usdt*', 'volume', 'up', 'sp', 'ft', 'upWit', 'bnDep']
        formatter = ['{}', '{:.6g}', '{:.6g}', '{:.6g}', '{:.6g}', '{:.6g}', '{:.6g}', '{}', '{}']
        self.widgets['treeViewUpToBn'] = MyTreeView(self.window, columns=_cols, show='headings', formatter=formatter)

        _cols = ['ticker', 'krw/usdt', 'krw/usdt*', 'volume', 'sp', 'up', 'ft', 'upWit', 'bnDep']
        formatter = ['{}', '{:.6g}', '{:.6g}', '{:.6g}', '{:.6g}', '{:.6g}', '{:.6g}', '{}', '{}']
        self.widgets['treeViewBnToUp'] = MyTreeView(self.window, columns=_cols, show='headings', formatter=formatter)

        self.transferDir = TransferDir.UpToBn
        self.widgets['btnToggleDir'] = tk.Button(self.window, text=self.transferDir)
        self.widgets['btnToggleDir'].pack(side='right')
        self.widgets['btnToggleDir'].config(command=self._toggleDir)

    def setDataUpToBn(self, data):
        # data[i] = MyList
        self.widgets['treeViewUpToBn'].updateTreeView(data)

    def setDataBnToUp(self, data):
        if data == PREPARING_DATA:
            self.widgets['treeViewBnToUp'].updateTreeView(data)
            return

        l = MAX_TABLE_LINES if len(data) > MAX_TABLE_LINES else len(data)
        try:
            for i in range(l):
                data[i]['price'] = Decimal(1) / data[i]['price']
                data[i]['_price'] = Decimal(1) / data[i]['_price']
            self.widgets['treeViewBnToUp'].updateTreeView(data)
        except Exception as e:
            print(e)

    def _toggleDir(self):
        if self.transferDir == TransferDir.UpToBn:
            self.transferDir = TransferDir.BnToUp
        elif self.transferDir == TransferDir.BnToUp:
            self.transferDir = TransferDir.UpToBn

        self.widgets['btnToggleDir'].config(text=str(self.transferDir))
        # ????.setTransDir()


class MyTreeView(ttk.Treeview):
    '''
    ttk.Treeview에 비해 추가된 기능
    데이터 테이블(이중배열) 던져주면 알아서 열 추가하는 기능.
    그와중에 format식 으로 서식 포맷팅 해주는 기능.
    '''

    def __init__(self, *args, **kwargs):
        if 'formatter' in kwargs.keys():
            self._formatter = kwargs['formatter']
            del kwargs['formatter']
        else:
            self._formatter = False

        super().__init__(*args, **kwargs)

        self._initTreeView(kwargs['columns'])

    def _initTreeView(self, _cols):
        for col in _cols:
            self.column(col, anchor="center", width=100)
            self.heading(col, text=col, anchor="center")

        self.pack(expand=True, fill='y')

    def updateTreeView(self, treeData):
        # treeData[i] = MyList
        lenView = len(self.get_children())
        lenData = len(treeData)
        lenData = lenData if lenData < MAX_TABLE_LINES else MAX_TABLE_LINES

        if lenView == lenData:
            pass
        elif lenView < lenData:
            for i in range(lenView, lenData):
                self.insert('', i, iid=i)
        elif lenView > lenData:
            for i in range(lenData, lenView):
                self.delete(i)

        for i in range(len(self.get_children())):
            self.item(item=i, values=self._formatLine(treeData[i]))

    def _formatLine(self, line: MyList):
        if not self._formatter:
            return line

        res = [None] * len(line)
        for i, item in enumerate(line):
            res[i] = self._formatter[i].format(item)

        return res


def main():
    app = tk.Tk()
    newWindow = tk.Toplevel(app)
    myViewWindow = MyViewWindow(newWindow)
    data = [['ticker', Decimal('1234.5678'), Decimal('1234.5678'), Decimal('1234.5678'), Decimal('80000000'),
             Decimal('0.00012345678'), Decimal('0.00012345678'), 'upWit', 'bnDep']] * 5
    myViewWindow.setDataUpToBn(data)
    app.mainloop()


if __name__ == "__main__":
    main()
