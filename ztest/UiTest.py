from tkinter import ttk
import tkinter as tk

app = tk.Tk()
app.geometry('600x300')

entry1 = tk.Entry(app)
entry1.grid(row = 0, column =0, rowspan=2, columnspan=3, sticky ='news', pady=15)

dummyLabel = tk.Label(app)
dummyLabel.grid(row=2, column=0, rowspan=1, columnspan=6, sticky ='news')

entry2 = tk.Entry(app)
entry2.grid(row = 3, column =0, rowspan=2, columnspan=3, sticky ='news', pady=15)

label1 = tk.Label(app, text='KRW')
label1.grid(row=0, column=3, rowspan=2, columnspan=1, sticky ='nws')

label2 = tk.Label(app, text='USDT')
label2.grid(row=3, column=3, rowspan=2, columnspan=1, sticky ='nws')

btn1 = tk.Button(app, text='UP -> BN')
btn1.grid(row=0, column=4, rowspan=2, columnspan=2, sticky ='news', pady=15)

btn2 = tk.Button(app, text='BN -> UP')
btn2.grid(row=3, column=4, rowspan=2, columnspan=2, sticky ='news', pady=15)

label3 = tk.Label(app, text='1. 매수단계')
label3.grid(row=2, column=6, rowspan=1, columnspan=2, sticky ='news')

label4 = tk.Label(app, text='2. 전송단계')
label4.grid(row=3, column=6, rowspan=1, columnspan=2, sticky ='news')

label5 = tk.Label(app, text='3. 매도단계')
label5.grid(row=4, column=6, rowspan=1, columnspan=2, sticky ='news')

btn3 = tk.Button(app, text='UP to BN')
btn3.grid(row=0, column=7, rowspan=1, columnspan=1, sticky ='ne')

app.columnconfigure(tuple(range(8)), weight=1)
app.rowconfigure(tuple(range(5)), weight=1)

app.mainloop()