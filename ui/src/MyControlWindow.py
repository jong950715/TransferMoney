from tkinter import ttk
import tkinter as tk

from work.TranferMoney import TransferState


class MyControlWindow:
    def __init__(self, window):
        self.window = window
        self.widgets = dict()
        self._loadWindow(self.window)

    def _loadWindow(self, newApp):
        newApp.geometry('600x300')

        self.widgets['entryKrwStr'] = tk.StringVar()
        self.widgets['entryKrw'] = tk.Entry(newApp, textvariable=self.widgets['entryKrwStr'])
        self.widgets['entryKrw'].grid(row=0, column=0, rowspan=2, columnspan=3, sticky='news', pady=15)


        self.widgets['dummyLabel'] = tk.Label(newApp)
        self.widgets['dummyLabel'].grid(row=2, column=0, rowspan=1, columnspan=6, sticky='news')

        self.widgets['entryUsdt'] = tk.Entry(newApp)
        self.widgets['entryUsdt'].grid(row=3, column=0, rowspan=2, columnspan=3, sticky='news', pady=15)

        self.widgets['label1'] = tk.Label(newApp, text='KRW')
        self.widgets['label1'].grid(row=0, column=3, rowspan=2, columnspan=1, sticky='nws')

        self.widgets['label2'] = tk.Label(newApp, text='USDT')
        self.widgets['label2'].grid(row=3, column=3, rowspan=2, columnspan=1, sticky='nws')

        self.widgets['btnUpToBn'] = tk.Button(newApp, text='UP -> BN')
        self.widgets['btnUpToBn'].grid(row=0, column=4, rowspan=2, columnspan=2, sticky='news', pady=15)

        self.widgets['btnBnToUp'] = tk.Button(newApp, text='BN -> UP')
        self.widgets['btnBnToUp'].grid(row=3, column=4, rowspan=2, columnspan=2, sticky='news', pady=15)

        self.widgets['labelBuying'] = tk.Label(newApp, text='1. 매수단계')
        self.widgets['labelBuying'].grid(row=2, column=6, rowspan=1, columnspan=2, sticky='news')

        self.widgets['label4'] = tk.Label(newApp, text='2. 전송단계')
        self.widgets['label4'].grid(row=3, column=6, rowspan=1, columnspan=2, sticky='news')

        self.widgets['label5'] = tk.Label(newApp, text='3. 매도단계')
        self.widgets['label5'].grid(row=4, column=6, rowspan=1, columnspan=2, sticky='news')

        self.widgets['btnToggleDir'] = tk.Button(newApp, text='UP to BN')
        self.widgets['btnToggleDir'].grid(row=0, column=7, rowspan=1, columnspan=1, sticky='ne')

        newApp.columnconfigure(tuple(range(8)), weight=1)
        newApp.rowconfigure(tuple(range(5)), weight=1)

    def setState(self, state):
        if state == TransferState.PREPARING:
            pass
        elif state == TransferState.STANDBY:
            pass
        elif state == TransferState.BUYING:
            self.widgets['labelBuying'].config(relief='ridge', borderwidth =3)
        elif state == TransferState.TRANSFERRING:
            pass
        elif state == TransferState.SELLING:
            pass
        elif state == TransferState.DONE:
            pass


def main():
    app = tk.Tk()
    newWindow = tk.Toplevel(app)
    myController = MyControlWindow(app)
    myController.widgets['btn3'].config(command=lambda: print("aa"))
    app.mainloop()


if __name__ == "__main__":
    main()
