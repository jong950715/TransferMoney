from decimal import Decimal

from common.SingleTonAsyncInit import SingleTonAsyncInit
from common.createTask import createTask
from data.ExGeneralInfo import ExGeneralInfo
from selfLib.UpClient import UpClient
from binance import AsyncClient as BnClient

from work.Order import FtOrder, SpOrder, UpOrder


class OrderManager(SingleTonAsyncInit):
    async def _asyncInit(self, upCli: UpClient, bnCli: BnClient, exInfo):
        FtOrder.initClass(client=bnCli, orderInfo=exInfo['ft'])
        SpOrder.initClass(client=bnCli, orderInfo=exInfo['sp'])
        UpOrder.initClass(client=upCli, orderInfo=exInfo['up'])

    async def submitOrderBatch(self, orderList):
        tasks = []
        for orderData in orderList:
            tasks.append(createTask(self.submitOrder(orderData)))

    async def submitOrder(self, orderData):
        # orderData = [ex, sym, price, qty]
        ex, sym, price, qty = orderData
        if ex == 'ft':
            order = FtOrder(sym=sym, price=price, qty=qty)
        elif ex == 'up':
            order = UpOrder(sym=sym, price=price, qty=qty)
        elif ex == 'sp':
            order = SpOrder(sym=sym, price=price, qty=qty)
        else:
            raise Exception('식별되지 않는 거래소 코드 입니다.', ex)

        await order.execute()
        # print("order 제출 테스토", orderData)
