import asyncio
from decimal import Decimal

from common.SingleTonAsyncInit import SingleTonAsyncInit
from common.createTask import createTask, RUNNING_FLAG
from config.MyConfigManager import MyConfigManager

from binance import AsyncClient as BnClient

from data.BalanceManager import BalanceManager
from data.dataCommons import tickerToUpbitSymbol, tickerToBnSymbol, toDecimal, tickerToSymbol
from selfLib.MyList import MyList
from selfLib.UpClient import UpClient

from data.BnFtWebSocket import BnFtWebSocket
from data.BnSpWebSocket import BnSpWebSocket
from data.ExGeneralInfo import ExGeneralInfo
from data.UpWebSocket import UpWebSocket
from ui.MyLogger import MyLogger
from work.Enums import TransferDir

BIG_DECIMAL_NUMBER = Decimal('inf')


class MyDataManager(SingleTonAsyncInit):
    async def _asyncInit(self, upCli: UpClient, bnCli: BnClient):
        self.logger = MyLogger.getLogger()
        self.upCli = upCli
        self.bnCli = bnCli

        self.exInfo = await ExGeneralInfo.createIns(upCli=self.upCli, bnCli=self.bnCli)
        await self.exInfo.updateAllInfo()

        self.tickers = self.exInfo.getTickers()

        self.logger.info('[시작] 웹소켓 설정을 시작합니다.')
        self.logger.info('\t 바이낸스 선물 웹소켓')
        self.bnFtWebSocket = await BnFtWebSocket.createIns(bnCli=self.bnCli, tickers=self.tickers)
        self.logger.info('\t 바이낸스 현물 웹소켓')
        self.bnSpWebSocket = await BnSpWebSocket.createIns(bnCli=self.bnCli, tickers=self.tickers)
        self.logger.info('\t 업비트 현물 웹소켓')
        self.upWebSocket = await UpWebSocket.createIns(tickers=self.tickers)
        self.logger.info('[끝] 웹소켓 설정이 끝났습니다.')

        self.balanceManager = await BalanceManager.createIns(upCli=self.upCli, bnCli=self.bnCli)

        self.upToBnDataCache = [['준비중']]
        self.dataCache = {TransferDir.UpToBn: [['준비중']],
                          TransferDir.BnToUp: [['준비중']]}

        self.cnt = {TransferDir.UpToBn: 0,
                    TransferDir.BnToUp: 0
                    }

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

    async def getDataByDir(self, _dir, includedTickers=None, remainNotional=None):
        if includedTickers is None:
            includedTickers = []

        if _dir == TransferDir.UpToBn:
            fromEx = 'up'
            toEx = 'sp'
            hedgeEx = 'ft'

            witEx = 'up'
            depEx = 'bn'
        elif _dir == TransferDir.BnToUp:
            fromEx = 'sp'
            toEx = 'up'
            hedgeEx = 'ft'

            witEx = 'bn'
            depEx = 'up'
        else:
            raise Exception('잘몬댐~', _dir)

        await self.awaitOrderBookUpdates()
        # ticker, krw/usdt, krw/usdt*, Volume, Upbit, bnSp, bnFt, upWithdraw, bnDeposit
        # KEYS1 = ['ticker', '_price', 'price', 'volume', 'upAsk', 'spBid', 'ftBid', 'upWithdraw', 'bnDeposit']
        # KEYS2 = ['ticker', '_price', 'price', 'volume', 'upBid', 'spAsk', 'ftBid', 'bnWithdraw', 'upDeposit']
        res = [MyList() for _ in range(len(self.tickers))]
        for i, tic in enumerate(self.tickers):
            fromSym = tickerToSymbol(fromEx, tic)
            toSym = tickerToSymbol(toEx, tic)
            hedgeSym = tickerToSymbol(hedgeEx, tic)

            fromAsk = toDecimal(self.orderBooks[fromEx][fromSym]['ask'][0][0])
            toBid = toDecimal(self.orderBooks[toEx][toSym]['bid'][0][0])
            hedgeBid = toDecimal(self.orderBooks[hedgeEx][hedgeSym]['bid'][0][0])

            fromAskQty = Decimal(self.orderBooks[fromEx][fromSym]['ask'][0][1])
            remainQty = remainNotional / fromAsk if remainNotional != None else fromAskQty

            '''###-###'''

            res[i]['ticker'] = tic
            res[i]['_price'] = fromAsk / toBid
            if tic in includedTickers:
                res[i]['price'] = fromAsk / toBid
            else:
                try:
                    res[i]['price'] = (fromAsk * remainQty) / (
                            toBid * (remainQty - self.getWalletInfo()[witEx][tic]['fee']))
                except ZeroDivisionError:
                    res[i][2] = BIG_DECIMAL_NUMBER
                except Exception as e:
                    raise e

            res[i]['volume'] = fromAskQty
            res[i]['{}Ask'.format(fromEx)] = fromAsk
            res[i]['{}Bid'.format(toEx)] = toBid
            res[i]['{}Bid'.format(hedgeEx)] = hedgeBid
            res[i]['{}Withdraw'.format(witEx)] = self.getWalletInfo()[witEx][tic]['withdraw']
            res[i]['{}Deposit'.format(depEx)] = self.getWalletInfo()[depEx][tic]['deposit']

        res.sort(
            key=lambda x: x['price'] if (x['price'] > 0 and x['{}Withdraw'.format(witEx)] and x[
                '{}Deposit'.format(depEx)]) else BIG_DECIMAL_NUMBER)

        self.dataCache[_dir] = res
        self.cnt[_dir] = 0

        return res

    def getDataByDirCached(self, _dir):
        return self.dataCache[_dir]

    async def awaitOrderBookUpdates(self):
        await self.bnFtWebSocket.awaitOrderBookUpdate()
        await self.bnSpWebSocket.awaitOrderBookUpdate()
        await self.upWebSocket.awaitOrderBookUpdate()

    async def _run(self):
        while True:
            await asyncio.sleep(0.1)
            self.cnt[TransferDir.UpToBn] += 1
            self.cnt[TransferDir.BnToUp] += 1

            if self.cnt[TransferDir.UpToBn] > 10:
                await self.getDataByDir(TransferDir.UpToBn)
            if self.cnt[TransferDir.BnToUp] > 10:
                await self.getDataByDir(TransferDir.BnToUp)

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
