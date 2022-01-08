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


class BnSpWebSocket(BaseWebSocket):
    async def _asyncInit(self, bnCli: AsyncClient, tickers):
        await super(BnSpWebSocket, self)._asyncInit()
        self.stream = ''
        self.bsm = BinanceSocketManager(bnCli)
        self.setWebSocketByTickers(tickers)

    def setWebSocketByTickers(self, tickers):
        self.stream = ''
        for ticker in tickers:
            self.addStream(tickerToBnSymbol(ticker), '{}@bookTicker')

    def addStream(self, sym: str, ev: str):
        stream = ev.format(sym.lower())
        if len(self.stream) == 0:
            self.stream = stream
        else:
            self.stream = self.stream + '/' + stream
        self.orderBook[sym.upper()]['event'] = asyncio.Event()

    def _getWebSocket(self):
        self.webSocket = self.bsm._get_socket(path=self.stream)
        return self.webSocket

    def consumer(self, msg):
        symbol = msg['s']

        ticker = bnSymbolToTicker(symbol)

        self.orderBook[symbol]['bid'][0] = [msg['b'], msg['B']]
        self.orderBook[symbol]['ask'][0] = [msg['a'], msg['A']]

        self.orderBook[symbol]['event'].set()


async def main():
    configKeys = getConfigKeys()
    client = await AsyncClient.create(configKeys['binance']['api_key'], configKeys['binance']['secret_key'])

    symbols = ['KLAY']
    bnSpWebSocket = await BnSpWebSocket.createIns(client, symbols)

    RUNNING_FLAG[0] = True
    await bnSpWebSocket.run()

    print(len('as'))


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
    print("끝")
