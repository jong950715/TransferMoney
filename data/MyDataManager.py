import asyncio
from decimal import Decimal

from common.SingleTonAsyncInit import SingleTonAsyncInit
from common.createTask import createTask, RUNNING_FLAG
from config.MyConfigManager import MyConfigManager

from binance import AsyncClient as BnClient

from data.BalanceManager import BalanceManager
from data.dataCommons import tickerToUpbitSymbol, tickerToBnSymbol, toDecimal
from selfLib.MyList import MyList
from selfLib.UpClient import UpClient

from data.BnFtWebSocket import BnFtWebSocket
from data.BnSpWebSocket import BnSpWebSocket
from data.ExGeneralInfo import ExGeneralInfo
from data.UpWebSocket import UpWebSocket

BIG_FLOAT_NUMBER = float('inf')


class MyDataManager(SingleTonAsyncInit):
    async def _asyncInit(self, upCli: UpClient, bnCli: BnClient):
        self.upCli = upCli
        self.bnCli = bnCli

        self.exInfo = await ExGeneralInfo.createIns(upCli=self.upCli, bnCli=self.bnCli)
        await self.exInfo.updateAllInfo()

        self.tickers = self.exInfo.getTickers()

        self.bnFtWebSocket = await BnFtWebSocket.createIns(bnCli=self.bnCli, tickers=self.tickers)
        self.bnSpWebSocket = await BnSpWebSocket.createIns(bnCli=self.bnCli, tickers=self.tickers)
        self.upWebSocket = await UpWebSocket.createIns(tickers=self.tickers)

        self.balanceManager = await BalanceManager.createIns(upCli=self.upCli, bnCli=self.bnCli)

        self.upToBnDataCache = [['준비중']]

        self.orderBooks = self._getOrderBook()

        self.run()

    async def updateBalances(self, tickers):
        await self.balanceManager.updateBalances(tickers)

    def getBalances(self):
        return self.balanceManager.getBalances()

    def getBnFtOrderBook(self):
        return self.bnFtWebSocket.getOrderBook()

    def getBnSpOrderBook(self):
        return self.bnSpWebSocket.getOrderBook()

    def getUpOrderBook(self):
        return self.upWebSocket.getOrderBook()

    def getOrderBooks(self):
        return self.orderBooks

    def _getOrderBook(self):
        up, sp, ft = self.getUpOrderBook(), self.getBnSpOrderBook(), self.getBnFtOrderBook()
        orderBook = {'up': up,
                     'sp': sp,
                     'ft': ft
                     }
        return orderBook

    def getWalletInfo(self):
        return self.exInfo.getWalletInfo()

    def getExInfo(self):
        return self.exInfo.getExInfo()

    def getTickers(self):
        return self.tickers

    def getUpToBnDataCached(self):
        return self.upToBnDataCache

    async def getUpToBnData(self, includedTickers=[], remainNotional=None):
        """
        데이터프레임을 인덱스로 관리하면 실수가능성이 높은것 같은데
        1. list-dict 쓴다.
        2. 자체 데이터프레임을 만든다. (문자->인덱스 변환해주는)

        2번 ㄱㄱ 해서 key를 문자나 int나 관계 없게하면 view에서도 쓰기 편함
        """
        await self.awaitOrderBookUpdates()
        # ticker, krw/usdt, krw/usdt*, Volume, Upbit, bnSp, bnFt, upWithdraw, bnDeposit
        # key : ticker, _price, price, volume, upAsk, spBid, ftBid, upWithdraw, bnDeposit
        res = [MyList() for _ in range(len(self.tickers))]
        for i, tic in enumerate(self.tickers):
            upSym = tickerToUpbitSymbol(tic)
            bnSym = tickerToBnSymbol(tic)
            upAsk, bnSpBid, bnFtBid = Decimal(self.orderBooks['up'][upSym]['ask'][0][0]), toDecimal(
                self.orderBooks['sp'][bnSym]['bid'][0][0]), toDecimal(
                self.orderBooks['ft'][bnSym]['bid'][0][0])
            upAskQty = Decimal(self.orderBooks['up'][upSym]['ask'][0][1])
            remainQty = remainNotional / upAsk if remainNotional != None else upAskQty

            '''###-###'''

            res[i]['ticker'] = tic
            res[i]['_price'] = upAsk / bnSpBid
            if tic in includedTickers:
                res[i]['price'] = upAsk / bnSpBid
            else:
                try:
                    res[i]['price'] = (upAsk * remainQty) / (
                            bnSpBid * (remainQty - self.getWalletInfo()['up'][tic]['fee']))
                except ZeroDivisionError:
                    res[i][2] = BIG_FLOAT_NUMBER
                except Exception as e:
                    raise e
            res[i]['volume'] = upAskQty
            res[i]['upAsk'] = upAsk
            res[i]['spBid'] = bnSpBid
            res[i]['ftBid'] = bnFtBid
            res[i]['upWithdraw'] = self.getWalletInfo()['up'][tic]['withdraw']
            res[i]['bnDeposit'] = self.getWalletInfo()['bn'][tic]['deposit']

        res.sort(
            key=lambda x: x['price'] if (x['price'] > 0 and x['upWithdraw'] and x['bnDeposit']) else BIG_FLOAT_NUMBER)

        self.upToBnDataCache = res

        return res

    async def awaitOrderBookUpdates(self):
        await self.bnFtWebSocket.awaitOrderBookUpdate()
        await self.bnSpWebSocket.awaitOrderBookUpdate()
        await self.upWebSocket.awaitOrderBookUpdate()

    async def _run(self):
        while True:
            await asyncio.sleep(5)

    def run(self):
        self.exInfo.run()
        self.bnFtWebSocket.run()
        self.bnSpWebSocket.run()
        self.upWebSocket.run()
        asyncio.get_event_loop().call_soon(createTask, self._run())
        RUNNING_FLAG[0] = True


async def main():
    dataManager = await MyDataManager.createIns()
    dataManager.run()
    while True:
        await asyncio.sleep(5)
        print("여기는 main문 입니다.")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
    print("끝")
