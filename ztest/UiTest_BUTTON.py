from tkinter import *


def Simpletoggle():
    if toggle_button.config('text')[-1] == 'BN TO UP':
        toggle_button.config(text='UP TO BN')
    else:
        toggle_button.config(text='BN TO UP')


ws = Tk()
ws.title("Python Guides")
ws.geometry("200x100")

toggle_button = Button(ws, text="UP TO BN", width=10, command=Simpletoggle)
toggle_button.pack(pady=10)

ws.mainloop()
