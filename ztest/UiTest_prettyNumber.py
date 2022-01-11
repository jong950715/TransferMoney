from decimal import Decimal, ConversionSyntax, InvalidOperation
from tkinter import *
import tkinter as tk

class EntryCommaNumber(tk.Entry):
    """
    숫자 읽기 좋은 Entry
    """

    def __init__(self, *args, **kwargs):
        self.str = tk.StringVar()
        kwargs['textvariable'] = self.str
        super().__init__(*args, **kwargs)
        self.bind("<KeyRelease>", self._format)
        self.comCnt = 0

    def _format(self, event):
        s = self.str.get()

        s = s.replace(',', '')
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
        pass


def main():
    app = tk.Tk()
    entry = EntryCommaNumber(app)
    entry.pack()
    app.mainloop()


main()

# def show_format(event):
#     print(event.widget.get())
#
#     # x = e1_str.get().replace(',', '')
#     # e1_str.set("{:,}".format(float(x)))
#     x = event.widget.get()
#     event.widget.config(text="{:,}".format(float(x)))
#
#
# my_w = tk.Tk()
# my_w.geometry("350x100")
# font1 = ('Times', 18, 'bold')
# sv = tk.StringVar()  # String varible
#
# e1_str = tk.StringVar()  # string variable
# e1 = tk.Entry(my_w, font=font1, width=20, textvariable=e1_str)
# e1.grid(row=1, column=1, padx=18, pady=5)
# # e1.Tex
# # e1.bind("<FocusOut>",show_format) # when tab is pressed
# e1.bind("<KeyRelease>", show_format)  # when key is released
# my_w.mainloop()  # Keep the window open
