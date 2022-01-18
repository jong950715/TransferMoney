import asyncio
from decimal import Decimal

from definitions import getRootDir
from selfLib.aiopyupbit import UpbitError
from binance.exceptions import BinanceAPIException

from common.SingleTonAsyncInit import SingleTonAsyncInit
from common.createTask import createTask
from data.ExGeneralInfo import ExGeneralInfo
from selfLib.UpClient import UpClient
from binance import AsyncClient as BnClient

from work.CheckPointManager import CheckPointManager
from work.Order import FtOrder, SpOrder, UpOrder

OM_PICKLE_FILE = '{0}/work/zOrderManager.pickle'.format(getRootDir())


class OrderManager(SingleTonAsyncInit, CheckPointManager):
    async def _asyncInit(self, upCli: UpClient, bnCli: BnClient, exInfo):
        self.upCli = upCli
        self.bnCli = bnCli

        FtOrder.initClass(client=bnCli, orderInfo=exInfo['ft'])
        SpOrder.initClass(client=bnCli, orderInfo=exInfo['sp'])
        UpOrder.initClass(client=upCli, orderInfo=exInfo['up'])

        self.ordersToBeCanceled = []

        self._initPickle(OM_PICKLE_FILE, ['ordersToBeCanceled'])

    async def submitOrderBatch(self, orderList):
        tasks = []
        for orderData in orderList:
            tasks.append(createTask(self.submitOrder(orderData)))
        if tasks:
            await asyncio.wait(tasks)

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

        res = await order.execute()
        if res:
            if ex == 'ft' or ex == 'sp':
                self.ordersToBeCanceled.append([ex, res['orderId'], sym])
            elif ex == 'up':
                self.ordersToBeCanceled.append([ex, res['uuid'], sym])
        self.saveCheckPoint()
        # print("order 제출 테스토", orderData)

    def getOrders(self):
        return self.ordersToBeCanceled

    async def cancelOrderBatch(self):
        tasks = []
        for orderData in self.ordersToBeCanceled:
            tasks.append(createTask(self.cancelOrder(*orderData)))
        self.ordersToBeCanceled = []
        self.saveCheckPoint()
        if tasks:
            await asyncio.wait(tasks)

    async def cancelOrder(self, ex, orderId, sym):
        try:
            if ex == 'ft':
                res = await self.bnCli.futures_cancel_order(symbol=sym, orderId=orderId)
            elif ex == 'up':
                res = await self.upCli.cancel_order(uuid=orderId)
            elif ex == 'sp':
                res = await self.bnCli.cancel_order(symbol=sym, orderId=orderId)
        except BinanceAPIException as e:
            if e.code != -2011:
                raise e
        except UpbitError as e:
            pass
        except Exception as e:
            raise e

    def done(self):
        self.saveGoodExitPoint()
