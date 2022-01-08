from data.dataCommons import tickerToBnSymbol, bnSymbolToTicker, tickerToUpbitSymbol, upbitSymbolToTicker
from selfLib.BaseWebSocket import BaseWebSocket
import asyncio
from binance import AsyncClient, DepthCacheManager, BinanceSocketManager
from binance.enums import FuturesType
import json
from collections import defaultdict
from common.SingleTonAsyncInit import SingleTonAsyncInit
from selfLib.UpbitSocketManager import UpbitSocketManager
from common.createTask import RUNNING_FLAG
from config.config import getConfigKeys


class UpWebSocket(BaseWebSocket):
    async def _asyncInit(self, tickers):
        await super(UpWebSocket, self)._asyncInit()
        self.subscribeData = [{"ticket": "ztest"}, {"type": "orderbook", "codes": []}, {"format": "SIMPLE"}]
        self.tickerToStreamFormat = '{}.3'
        self.usm = UpbitSocketManager()
        self.setWebSocketByTickers(tickers)

    def setWebSocketByTickers(self, tickers):
        self.subscribeData[1]['codes'] = []
        for ticker in tickers:
            self.addStream(tickerToUpbitSymbol(ticker))

    def addStream(self, sym: str):
        stream = str(self.tickerToStreamFormat).format(sym)
        self.subscribeData[1]['codes'].append(stream)
        self.orderBook[sym]['event'] = asyncio.Event()

    def _getWebSocket(self):
        self.webSocket = self.usm._get_socket(subscribe_data=self.subscribeData)
        return self.webSocket

    def consumer(self, msg):
        sym = msg['cd']
        books = msg['obu']
        for i, book in enumerate(books):
            self.orderBook[sym]['bid'][i] = [book['bp'], book['bs']]
            self.orderBook[sym]['ask'][i] = [book['ap'], book['as']]

        self.orderBook[sym]['event'].set()


async def main():
    tickers = ['1INCH', 'AAVE', 'ADA', 'ALGO', 'ANKR', 'ATOM', 'AXS', 'BAT', 'BCH', 'BTC', 'BTT', 'CHZ', 'CVC', 'DOGE', 'DOT', 'ENJ', 'EOS', 'ETC', 'ETH', 'HBAR', 'ICX', 'IOST', 'IOTA', 'KAVA', 'KNC', 'LINK', 'LTC', 'MANA', 'MATIC', 'MTL', 'NEAR', 'NEO', 'NU', 'OMG', 'ONT', 'QTUM', 'SAND', 'SC', 'SOL', 'SRM', 'STMX', 'STORJ', 'SXP', 'THETA', 'TRX', 'VET', 'WAVES', 'XEM', 'XLM', 'XRP', 'XTZ', 'ZIL', 'ZRX']
    upWebSocket = await UpWebSocket.createIns(tickers)

    RUNNING_FLAG[0] = True
    upWebSocket.run()

    while True:
        print("여기는 main문 입니다.")
        print(upWebSocket.getOrderBook())
        await asyncio.sleep(1)
        await upWebSocket.awaitOrderBookUpdate()


    print(len('as'))


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
    print("끝")
