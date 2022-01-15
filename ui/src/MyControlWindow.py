from tkinter import ttk
import tkinter as tk

from ui.src.EntryCommaNumber import EntryCommaNumber
from work.Enums import TransferState


class MyControlWindow:
    def __init__(self, window):
        self.window = window
        self.widgets = dict()
        self._loadWindow(self.window)
        self.prevState = TransferState.PREPARING

    def _loadWindow(self, newApp):
        newApp.geometry('600x300')

        self.widgets['entryKrw'] = EntryCommaNumber(newApp)
        self.widgets['entryKrw'].grid(row=0, column=0, rowspan=2, columnspan=3, sticky='news', pady=15)

        self.widgets['dummyLabel'] = tk.Label(newApp)
        self.widgets['dummyLabel'].grid(row=2, column=0, rowspan=2, columnspan=6, sticky='news')

        self.widgets['entryUsdt'] = EntryCommaNumber(newApp)
        self.widgets['entryUsdt'].grid(row=4, column=0, rowspan=2, columnspan=3, sticky='news', pady=15)

        self.widgets['label1'] = tk.Label(newApp, text='KRW')
        self.widgets['label1'].grid(row=0, column=3, rowspan=2, columnspan=1, sticky='nws')

        self.widgets['label2'] = tk.Label(newApp, text='USDT')
        self.widgets['label2'].grid(row=4, column=3, rowspan=2, columnspan=1, sticky='nws')

        self.widgets['btnUpToBn'] = tk.Button(newApp, text='UP -> BN')
        self.widgets['btnUpToBn'].grid(row=0, column=4, rowspan=2, columnspan=2, sticky='news', pady=15)

        self.widgets['btnBnToUp'] = tk.Button(newApp, text='BN -> UP')
        self.widgets['btnBnToUp'].grid(row=4, column=4, rowspan=2, columnspan=2, sticky='news', pady=15)

        self.widgets['labelPREPARING'] = tk.Label(newApp, text='0. 준비중')
        self.widgets['labelPREPARING'].grid(row=0, column=6, rowspan=1, columnspan=2, sticky='news')

        self.widgets['labelSTANDBY'] = tk.Label(newApp, text='1. 준비완료')
        self.widgets['labelSTANDBY'].grid(row=1, column=6, rowspan=1, columnspan=2, sticky='news')

        self.widgets['labelBUYING'] = tk.Label(newApp, text='2. 매수단계')
        self.widgets['labelBUYING'].grid(row=2, column=6, rowspan=1, columnspan=2, sticky='news')

        self.widgets['labelTRANSFERRING'] = tk.Label(newApp, text='3. 전송단계')
        self.widgets['labelTRANSFERRING'].grid(row=3, column=6, rowspan=1, columnspan=2, sticky='news')

        self.widgets['labelSELLING'] = tk.Label(newApp, text='4. 매도단계')
        self.widgets['labelSELLING'].grid(row=4, column=6, rowspan=1, columnspan=2, sticky='news')

        self.widgets['labelDONE'] = tk.Label(newApp, text='5. 완료')
        self.widgets['labelDONE'].grid(row=5, column=6, rowspan=1, columnspan=2, sticky='news')

        newApp.columnconfigure(tuple(range(8)), weight=1)
        newApp.rowconfigure(tuple(range(6)), weight=1)

    def setState(self, state):
        prevName = 'label{0}'.format(self.prevState)
        labelName = 'label{0}'.format(state)

        if state == TransferState.PREPARING:
            pass
        elif state == TransferState.STANDBY:
            pass
        elif state == TransferState.BUYING:
            pass
        elif state == TransferState.TRANSFERRING:
            pass
        elif state == TransferState.SELLING:
            pass
        elif state == TransferState.DONE:
            pass

        self.widgets[prevName].config(relief='flat')
        self.widgets[labelName].config(relief='ridge', borderwidth=3)

        self.prevState = state


def main():
    app = tk.Tk()
    newWindow = tk.Toplevel(app)
    myController = MyControlWindow(app)
    myController.widgets['btn3'].config(command=lambda: print("aa"))
    app.mainloop()


if __name__ == "__main__":
    main()
