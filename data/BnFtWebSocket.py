from decimal import Decimal
from data.dataCommons import tickerToBnSymbol, bnSymbolToTicker
from selfLib.BaseWebSocket import BaseWebSocket
import asyncio
from binance import AsyncClient, DepthCacheManager, BinanceSocketManager
from binance.enums import FuturesType
import json
from collections import defaultdict
from common.SingleTonAsyncInit import SingleTonAsyncInit
from common.createTask import RUNNING_FLAG
from config.config import getConfigKeys


class BnFtWebSocket(BaseWebSocket):
    async def _asyncInit(self, bnCli: AsyncClient, tickers):
        await super(BnFtWebSocket, self)._asyncInit()
        self.stream = ''
        self.bsm = BinanceSocketManager(bnCli)
        self._setWebSocketByTickers(tickers)

    def _setWebSocketByTickers(self, tickers):
        self.stream = ''
        for ticker in tickers:
            self._addStream(tickerToBnSymbol(ticker), '{}@depth5@100ms')

    def _addStream(self, sym: str, ev: str):
        stream = ev.format(sym.lower())
        if len(self.stream) == 0:
            self.stream = stream
        else:
            self.stream = self.stream + '/' + stream
        self.orderBook[sym.upper()]['event'] = asyncio.Event()
        
    #이하 오버라이드
    def _getWebSocket(self):
        self.webSocket = self.bsm._get_futures_socket(path=self.stream, futures_type=FuturesType.USD_M)
        return self.webSocket

    def consumer(self, msg):
        symbol = msg['data']['s']

        for i, b in enumerate(msg['data']['b']):  # buy 삽니다
            self.orderBook[symbol]['bid'][i] = b
        for i, a in enumerate(msg['data']['a']):  # sell 팝니다
            self.orderBook[symbol]['ask'][i] = a

        self.orderBook[symbol]['event'].set()


async def main():
    configKeys = getConfigKeys()
    client = await AsyncClient.create(configKeys['binance']['api_key'], configKeys['binance']['secret_key'])

    tickers = ['1INCH', 'AAVE', 'ADA', 'ALGO', 'ANKR', 'ATOM', 'AXS', 'BAT', 'BCH', 'BTC', 'BTT', 'CHZ', 'CVC', 'DOGE', 'DOT', 'ENJ', 'EOS', 'ETC', 'ETH', 'HBAR', 'ICX', 'IOST', 'IOTA', 'KAVA', 'KNC', 'LINK', 'LTC', 'MANA', 'MATIC', 'MTL', 'NEAR', 'NEO', 'NU', 'OMG', 'ONT', 'QTUM', 'SAND', 'SC', 'SOL', 'SRM', 'STMX', 'STORJ', 'SXP', 'THETA', 'TRX', 'VET', 'WAVES', 'XEM', 'XLM', 'XRP', 'XTZ', 'ZIL', 'ZRX']
    bnFtWebSocket = await BnFtWebSocket.createIns(client, tickers)

    RUNNING_FLAG[0] = True
    bnFtWebSocket.run()

    while True:
        print("여기는 main문 입니다.")
        print(list(bnFtWebSocket.getOrderBook().values()))
        await asyncio.sleep(1)
        await bnFtWebSocket.awaitOrderBookUpdate()

    print(len('as'))


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
    print("끝")
