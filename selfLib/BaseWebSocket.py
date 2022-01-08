
import asyncio
from binance import AsyncClient, DepthCacheManager, BinanceSocketManager
from binance.enums import FuturesType
import json
from collections import defaultdict
from common.SingleTonAsyncInit import SingleTonAsyncInit
from common.createTask import RUNNING_FLAG, createTask
from config.config import getConfigKeys

MaxOderBookDepth = 10
class BaseWebSocket(SingleTonAsyncInit):
    async def _asyncInit(self, *args, **kwargs):
        # self.orderBook['symbol']['ask'] = [
        #                                       ['price', 'qty'],
        #                                       ['price', 'qty'],
        #                                       ['price', 'qty'], ...]
        self.orderBook = defaultdict(lambda: defaultdict(lambda: [[0, 0]] * MaxOderBookDepth)) #  bid = want to buy, ask = want to sell

    def getOrderBook(self):
        return self.orderBook

    async def awaitOrderBookUpdate(self):
        books = list(self.orderBook.values())
        tasks = [asyncio.create_task(book['event'].wait()) for book in books]
        returns, pending = await asyncio.wait(tasks)

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