import asyncio
from collections import defaultdict
from decimal import Decimal
from enum import Enum

from common.SingleTonAsyncInit import SingleTonAsyncInit
from common.createTask import createTask
from data.MyDataManager import MyDataManager
from data.dataCommons import toDecimal, tickerToSymbol
from definitions import getRootDir
from work.CheckPointManager import CheckPointManager
from work.OrderManager import OrderManager

UPBIT_TOL_KRW = Decimal(50000)
BINAN_TOL_USD = Decimal(50)

TM_PICKLE_FILE = '{0}/work/TransferMoney.pickle'.format(getRootDir())


class TransferDir(Enum):
    UpToBn = 'Up To Bn'
    BnToUp = 'Bn To Up'

    def __str__(self):
        return self.value


class TransferState(Enum):
    PREPARING = 'PREPARING'
    STANDBY = 'STANDBY'
    BUYING = 'BUYING'
    TRANSFERRING = 'TRANSFERRING'
    SELLING = 'SELLING'
    DONE = 'DONE'

    def __str__(self):
        return self.value


class TransferMoney(SingleTonAsyncInit, CheckPointManager):
    async def _asyncInit(self, dataManager: MyDataManager, orderManager: OrderManager):
        self.dataManger = dataManager
        self.orderManager = orderManager

        self.runState = TransferState.PREPARING

        self.orderBooks = dataManager.getOrderBooks()
        self.balances = dataManager.getBalances()

        self._setPickleFile(TM_PICKLE_FILE)
        self._setPickleList(['_dir', 'totalNotional', 'remainNotional',
                             'buyingTickers', 'targetBalances', 'runState'])
        self.checkUnPredictedExit()

        self.run()

    def run(self):
        asyncio.get_event_loop().call_soon(createTask, self._run())

    async def _run(self):
        while True:
            await asyncio.sleep(0.05)
            if self.runState == TransferState.PREPARING:
                await self.runPreparing()
            elif self.runState == TransferState.STANDBY:
                await self.runStandby()
            elif self.runState == TransferState.BUYING:
                await self.runBuying()
            elif self.runState == TransferState.TRANSFERRING:
                await self.runTransferring()
            elif self.runState == TransferState.SELLING:
                await self.runSelling()
            elif self.runState == TransferState.DONE:
                await self.runDone()

    async def runPreparing(self):
        if self.dataManger:
            self.runState = TransferState.STANDBY

    async def runStandby(self):
        pass

    def startTransfer(self, _dir: TransferDir, notional):
        if self.runState == TransferState.STANDBY:
            self.initBuying(_dir, notional)
        # state 검사 로직 추가

    def initBuying(self, _dir, notional):
        self._dir = _dir

        self.totalNotional = notional
        self.remainNotional = notional

        self.buyingTickers = []

        self.targetBalances = {'up': defaultdict(Decimal),
                               'sp': defaultdict(Decimal),
                               'ft': defaultdict(Decimal)
                               }

        self.runState = TransferState.BUYING

        self.saveCheckPoint()

    async def runBuying(self):
        # 방향 반응형으로 만들고, GUI까지 테스트 고고하자, 피클링까지 고민해야됨..
        await asyncio.sleep(3)
        await self.traceTargetBalance()  # 별도로 백그라운드로 뺄 수도 있음
        await self._runBuying()

        if self.isBuyingFinished():
            self.initTransferring()

    async def cancelAllOrders(self):
        await self.orderManager.cancelOrderBatch()

    async def traceTargetBalance(self):
        """
        피클링 목록
        self.dir
        self.totalNotional
        self.remainNotional
        self.buyingTickers
        self.targetBalances
        self.runState

        방향성 목록
        upReal
        ftReal
        upTarget
        ftTarget
        upSym
        ftSym
        upQty
        ftQty
        upPrice
        ftPrice
        """
        if self._dir == TransferDir.UpToBn:
            buyEx = 'up'
            sellEx = 'ft'
        elif self._dir == TransferDir.BnToUp:
            buyEx = 'sp'
            sellEx = 'ft'
        else:
            raise Exception('dir이 이상해..', self._dir)

        await self.dataManger.updateBalances(tickers=self.buyingTickers)
        await self.cancelAllOrders()

        orderList = []
        for ticker in self.buyingTickers:
            buyBalanceQty = self._getBalance(buyEx, ticker)
            sellBalanceQty = self._getBalance(sellEx, ticker)
            buyTargetQty = self.targetBalances[buyEx][ticker]
            sellTargetQty = self.targetBalances[sellEx][ticker]

            buySym = tickerToSymbol(buyEx, ticker)
            sellSym = tickerToSymbol(sellEx, ticker)
            buyQty = buyTargetQty - buyBalanceQty
            sellQty = sellTargetQty - sellBalanceQty
            buyPrice = self._getBestBidAskPrice(buyEx, buySym, 'ask')
            sellPrice = self._getBestBidAskPrice(sellEx, sellSym, 'bid')

            orderList.append([buyEx, buySym, buyPrice, buyQty])
            orderList.append([sellEx, sellSym, sellPrice, sellQty])

        self.saveCheckPoint()
        await self.orderManager.submitOrderBatch(orderList)

    def _getBalance(self, ex, ticker):
        if ex == 'up':
            return Decimal(self.balances[ex][ticker])
        elif ex == 'sp' or ex == 'ft':
            return self.balances[ex][ticker]

    def _getBestBidAskPrice(self, ex, sym, bidAsk):
        if ex == 'up':
            return Decimal(self.orderBooks[ex][sym][bidAsk][0][0])
        elif ex == 'sp' or ex == 'ft':
            return toDecimal(self.orderBooks[ex][sym][bidAsk][0][0])

    async def _runBuying(self):
        """
        방향성
        UPBIT_TOL_KRW
        sym
        price
        notional
        qty
        ftSym
        ftPrice
        """
        if self._dir == TransferDir.UpToBn:
            fromTolNotional = UPBIT_TOL_KRW
            buyEx = 'up'
            sellEx = 'ft'
        elif self._dir == TransferDir.BnToUp:
            fromTolNotional = BINAN_TOL_USD
            buyEx = 'sp'
            sellEx = 'ft'
        else:
            raise Exception('dir이 이상해..', self._dir)

        if self.remainNotional < fromTolNotional:
            return

        # data[i] = MyList
        # KEYS1 = ['ticker', '_price', 'price', 'volume', 'upAsk', 'spBid', 'ftBid', 'upWithdraw', 'bnDeposit']
        # KEYS2 = ['ticker', '_price', 'price', 'volume', 'upBid', 'spAsk', 'ftAsk', 'bnWithdraw', 'upDeposit']

        data = await self.dataManger.getUpToBnData(includedTickers=self.buyingTickers,
                                                   remainNotional=self.remainNotional)
        data = data[0]

        ticker = data['ticker']
        buySym = tickerToSymbol(buyEx, ticker)
        buyPrice = data['{}Ask'.format(buyEx)]
        buyMaxNotional = data['volume'] * data['{}Ask'.format(buyEx)]
        qty = data['volume'] if buyMaxNotional < self.remainNotional else self.remainNotional / data[
            '{}Ask'.format(buyEx)]

        sellSym = tickerToSymbol(sellEx, ticker)
        sellPrice = data['{}Bid'.format(sellEx)]

        orderList = [[buyEx, buySym, buyPrice, qty],
                     [sellEx, sellSym, sellPrice, -qty]]

        self.saveCheckPoint()
        await self.orderManager.submitOrderBatch(orderList)

        self.targetBalances[buyEx][ticker] += qty
        self.targetBalances[sellEx][ticker] -= qty
        self.remainNotional -= qty * buyPrice
        self.buyingTickers.append(ticker)
        self.saveCheckPoint()

    def _saveBuying(self):
        """
        피클링 목록
        self.dir
        self.totalNotional
        self.remainNotional
        self.buyingTickers
        self.targetBalances
        self.runState
        """
        pass

    def isBuyingFinished(self):
        # 탈출조건
        '''
        remain notional이 다 소진되었는데,
        실제 balace의 notional과
        타겟 balace의 notional이 오차범위 내에 있으면 탈출
        '''
        """
        방향성 목록
        UPBIT_TOL_KRW
        BINAN_TOL_USD
        upNotional
        ftNotional
        upTarget
        ftTarget
        upDiff
        ftDiff
        """
        if self._dir == TransferDir.UpToBn:
            buyTolNotional = UPBIT_TOL_KRW
            sellTolNotional = BINAN_TOL_USD
            buyEx = 'up'
            sellEx = 'ft'
        elif self._dir == TransferDir.BnToUp:
            buyTolNotional = BINAN_TOL_USD
            sellTolNotional = BINAN_TOL_USD
            buyEx = 'sp'
            sellEx = 'ft'
        else:
            raise Exception('dir이 이상해..', self._dir)

        if self.remainNotional > buyTolNotional:  # Decimal vs int는 가능
            return False

        buyNotional = Decimal()
        sellNotional = Decimal()
        buyTargetNotional = Decimal()
        sellTargetNotional = Decimal()
        for ticker in self.buyingTickers:
            buySym = tickerToSymbol(buyEx, ticker)
            sellSym = tickerToSymbol(sellEx, ticker)

            buyPrice = self._getBestBidAskPrice(buyEx, buySym, 'ask')
            sellPrice = self._getBestBidAskPrice(sellEx, sellSym, 'bid')

            buyBalanceQty = self._getBalance(buyEx, ticker)
            sellBalanceQty = self._getBalance(sellEx, ticker)

            buyNotional += buyBalanceQty * buyPrice
            buyTargetNotional += self.targetBalances[buyEx][ticker] * buyPrice

            sellNotional += sellBalanceQty * sellPrice
            sellTargetNotional += self.targetBalances[sellEx][ticker] * sellPrice

        buyDiff = buyTargetNotional - buyNotional
        sellDiff = sellTargetNotional - sellNotional

        if abs(buyDiff) < buyTolNotional and abs(sellDiff) < sellTolNotional:
            return True
        else:
            return False

    def initTransferring(self):
        self.runState = TransferState.TRANSFERRING
        self.saveCheckPoint()

    async def runTransferring(self):
        pass

    async def runSelling(self):
        pass

    async def runDone(self):
        pass

    def getState(self):
        return self.runState

    def order(self, *args):
        print('order', args)


async def main():
    dataManager = await MyDataManager.createIns()
    transferMoney = await TransferMoney.createIns(dataManager)
    transferMoney.startTransfer(_dir=TransferDir.UpToBn, notional=1000000)

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
