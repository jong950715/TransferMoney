from decimal import Decimal

qty = Decimal(6060.606060610000126803398971)
qtyStep = Decimal(1.0000000000000000209225608301284726753266340892878361046314239501953125E-8)

n = round(qty/qtyStep)
print(n)

newQty = n *qtyStep
print(newQty)
print(newQty%qtyStep)

#
#
# C:\Users\user\Dropbox\파이썬\TransferMoney\venv\Scripts\python.exe C:/Users/user/Dropbox/파이썬/TransferMoney/main.py
# Traceback (most recent call last):
#   File "C:\Users\user\Dropbox\파이썬\TransferMoney\common\createTask.py", line 21, in _handle_task_result
#     task.result()
#   File "C:\Users\user\Dropbox\파이썬\TransferMoney\work\OrderManager.py", line 35, in submitOrder
#     await order.execute()
#   File "C:\Users\user\Dropbox\파이썬\TransferMoney\work\Order.py", line 87, in execute
#     if self.fitByRound() is False:
#   File "C:\Users\user\Dropbox\파이썬\TransferMoney\work\Order.py", line 43, in fitByRound
#     return self.validate()
#   File "C:\Users\user\Dropbox\파이썬\TransferMoney\work\Order.py", line 65, in validate
#     raise Exception(message)  # round를 했는데 있을 수 없는 상황 이므로 Exception
# Exception:  =====수량 정밀도 에러=====	 sym : KRW-SC	 qty : 6060.606060610000126803398971	 qtyStep : 1.0000000000000000209225608301284726753266340892878361046314239501953125E-8	 =====수량 정밀도 에러=====
#
#
# #ORDER#
#  sym : SCUSDT
#  p : 0.013430
#  q : 6061.000000
# Traceback (most recent call last):
#   File "C:\Users\user\Dropbox\파이썬\TransferMoney\common\createTask.py", line 21, in _handle_task_result
#     task.result()
#   File "C:\Users\user\Dropbox\파이썬\TransferMoney\work\OrderManager.py", line 35, in submitOrder
#     await order.execute()
#   File "C:\Users\user\Dropbox\파이썬\TransferMoney\work\Order.py", line 87, in execute
#     if self.fitByRound() is False:
#   File "C:\Users\user\Dropbox\파이썬\TransferMoney\work\Order.py", line 43, in fitByRound
#     return self.validate()
#   File "C:\Users\user\Dropbox\파이썬\TransferMoney\work\Order.py", line 65, in validate
#     raise Exception(message)  # round를 했는데 있을 수 없는 상황 이므로 Exception
# Exception:  =====수량 정밀도 에러=====	 sym : KRW-SC	 qty : 6060.606060610000126803398971	 qtyStep : 1.0000000000000000209225608301284726753266340892878361046314239501953125E-8	 =====수량 정밀도 에러=====
#
#
# Traceback (most recent call last):
#   File "C:\Users\user\Dropbox\파이썬\TransferMoney\common\createTask.py", line 21, in _handle_task_result
#     task.result()
#   File "C:\Users\user\Dropbox\파이썬\TransferMoney\ui\MyGuiManager.py", line 81, in _run
#     await self.updateGui()
#   File "C:\Users\user\Dropbox\파이썬\TransferMoney\ui\MyGuiManager.py", line 66, in updateGui
#     await self.updateView()
#   File "C:\Users\user\Dropbox\파이썬\TransferMoney\ui\MyGuiManager.py", line 71, in updateView
#     self.viewWindow.setDataUpToBn(await self.getUpToBnData())
#   File "C:\Users\user\Dropbox\파이썬\TransferMoney\ui\MyGuiManager.py", line 61, in getUpToBnData
#     return await self.dataManager.getUpToBnData()
#   File "C:\Users\user\Dropbox\파이썬\TransferMoney\data\MyDataManager.py", line 91, in getUpToBnData
#     await self.awaitOrderBookUpdates()
#   File "C:\Users\user\Dropbox\파이썬\TransferMoney\data\MyDataManager.py", line 133, in awaitOrderBookUpdates
#     await self.bnFtWebSocket.awaitOrderBookUpdate()
#   File "C:\Users\user\Dropbox\파이썬\TransferMoney\selfLib\BaseWebSocket.py", line 27, in awaitOrderBookUpdate
#     tasks = [asyncio.create_task(book['event'].wait()) for book in books]
#   File "C:\Users\user\Dropbox\파이썬\TransferMoney\selfLib\BaseWebSocket.py", line 27, in <listcomp>
#     tasks = [asyncio.create_task(book['event'].wait()) for book in books]
# AttributeError: 'list' object has no attribute 'wait'
#
#
# Process finished with exit code -1