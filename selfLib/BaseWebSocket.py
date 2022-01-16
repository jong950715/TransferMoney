import asyncio
from decimal import Decimal

from binance import AsyncClient, DepthCacheManager, BinanceSocketManager
from binance.enums import FuturesType
import json
from collections import defaultdict
from common.SingleTonAsyncInit import SingleTonAsyncInit
from common.createTask import RUNNING_FLAG, createTask
from config.config import getConfigKeys
from ui.MyLogger import MyLogger

MaxOderBookDepth = 10
TIME_OUT_SEC = 10


class BaseWebSocket(SingleTonAsyncInit):
    async def _asyncInit(self, *args, **kwargs):
        # self.orderBook['symbol']['ask'] = [
        #                                       ['price', 'qty'],
        #                                       ['price', 'qty'],
        #                                       ['price', 'qty'], ...]
        self.orderBook = defaultdict(lambda: defaultdict(
            lambda: [[Decimal(), Decimal()]] * MaxOderBookDepth))  # bid = want to buy, ask = want to sell

    def getOrderBook(self):
        return self.orderBook

    async def awaitOrderBookUpdate(self):
        books = list(self.orderBook.values())
        try:
            tasks = [asyncio.create_task(book['event'].wait()) for book in books]
        except Exception as e:
            print(books)
        returns, pending = await asyncio.wait(tasks, timeout=TIME_OUT_SEC)

        if pending:
            self.logPending()
            return False
        else:
            return True

    def logPending(self):
        for symbol, book in self.orderBook.items():
            if not (book['event'].is_set()):
                MyLogger.getLogger().info('{0}이 지연되고 있습니다. 제외시켜주세요.'.format(symbol))

    def clearAwaitEvent(self):
        for ticker, book in self.orderBook.items():
            book['event'].clear()

    def _getWebSocket(self):
        pass

    async def _run(self):
        async with self._getWebSocket() as ts:
            while RUNNING_FLAG[0]:
                msg = await ts.recv()
                self.consumer(msg)

    def run(self):
        asyncio.get_event_loop().call_soon(createTask, self._run())

    def consumer(self, msg):
        pass
