from decimal import Decimal, ConversionSyntax, InvalidOperation
from tkinter import *
import tkinter as tk


class EntryCommaNumber(tk.Entry):
    """
    숫자 읽기 좋은 Entry
    """

    def __init__(self, *args, **kwargs):
        self.str = tk.StringVar()
        self.str.set('0')
        kwargs['textvariable'] = self.str
        super().__init__(*args, **kwargs)
        self.bind("<KeyRelease>", self._format)
        self.comCnt = 0

    def _format(self, event):
        s = self.str.get().replace(',', '')

        try:
            s = "{:,}".format(Decimal(s))
        except (ConversionSyntax, InvalidOperation):
            pass
        except Exception as e:
            raise e
        self.str.set(s)

        pCnt = self.comCnt
        self.comCnt = s.count(',')

        position = self.index(INSERT)
        self.icursor(position + self.comCnt - pCnt)

    def get(self):
        return Decimal(self.str.get().replace(',', ''))

def test():
    app = tk.Tk()
    entry = EntryCommaNumber(app)
    entry.pack()

    cnt = 0
    while True:
        app.update()
        cnt += 1
        if cnt > 100000:
            cnt = 0
            print(entry.get())



if __name__ == "__main__":
    test()