import asyncio
from collections import defaultdict
from decimal import Decimal
from enum import Enum

from common.SingleTonAsyncInit import SingleTonAsyncInit
from common.createTask import createTask
from data.MyDataManager import MyDataManager
from data.dataCommons import tickerToUpbitSymbol, toDecimal, tickerToBnSymbol, symbolToTicker, tickerToSymbol
from work.OrderManager import OrderManager

UPBIT_TOL_KRW = 50000
BINAN_TOL_USD = 50

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


class TransferMoney(SingleTonAsyncInit):
    async def _asyncInit(self, dataManager: MyDataManager, orderManager: OrderManager):
        self.dataManger = dataManager
        self.orderManager = orderManager

        self.runState = TransferState.PREPARING

        self.orderBooks = dataManager.getOrderBooks()
        self.balances = dataManager.getBalances()

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

    def startTransfer(self, dir: TransferDir, notional):
        # state 검사 로직 추가
        self.dir = dir
        self.totalNotional = notional
        self.remainNotional = notional

        self.initBuying()

    def initBuying(self):
        self.buyingTickers = []

        self.targetBalance = {'up': defaultdict(Decimal),
                              'sp': defaultdict(Decimal),
                              'ft': defaultdict(Decimal)
                              }

        self.runState = TransferState.BUYING
        self.cnt = 0

    async def runBuying(self):
        # 방향 반응형으로 만들고, GUI까지 테스트 고고하자
        await asyncio.sleep(3)
        await self.traceTargetBalance()  # 별도로 백그라운드로 뺄 수도 있음
        await self._runBuying()

        if self.isBuyingFinished():
            self.initTransferring()

    async def cancelAllOrders(self):
        pass

    async def traceTargetBalance(self):
        await self.dataManger.updateBalances(tickers=self.buyingTickers)
        await self.cancelAllOrders()

        orderList = []
        for ticker in self.buyingTickers:
            upReal = Decimal(self.balances['up'][ticker])
            ftReal = self.balances['ft'][ticker]
            upTarget = self.targetBalance['up'][ticker]
            ftTarget = self.targetBalance['ft'][ticker]

            upSym = tickerToUpbitSymbol(ticker)
            ftSym = tickerToBnSymbol(ticker)
            upQty = upTarget - upReal
            ftQty = ftTarget - ftReal
            upPrice = Decimal(self.orderBooks['up'][upSym]['ask'][0][0])
            ftPrice = toDecimal(self.orderBooks['ft'][upSym]['bid'][0][0])

            orderList.append(['up', upSym, upPrice, upQty])
            orderList.append(['ft', ftSym, ftPrice, ftQty])

        await self.orderManager.submitOrderBatch(orderList)

    async def _runBuying(self):
        if self.remainNotional < UPBIT_TOL_KRW:
            return

        # data[i] = MyList
        # KEYS1 = ['ticker', '_price', 'price', 'volume', 'upAsk', 'spBid', 'ftBid', 'upWithdraw', 'bnDeposit']
        # KEYS2 = ['ticker', '_price', 'price', 'volume', 'upBid', 'spAsk', 'ftAsk', 'bnWithdraw', 'upDeposit']

        data = await self.dataManger.getUpToBnData(includedTickers=self.buyingTickers,
                                                   remainNotional=self.remainNotional)
        data = data[0]

        ticker = data['ticker']
        sym = tickerToSymbol('up', ticker)
        price = data['upAsk']
        notional = data['volume'] * data['upAsk']
        qty = data['volume'] if notional < self.remainNotional else self.remainNotional / data['upAsk']

        ftSym = tickerToSymbol('ft', ticker)
        ftPrice = data['ftBid']

        orderList = [['up', sym, price, qty],
                     ['ft', ftSym, ftPrice, qty]]
        await self.orderManager.submitOrderBatch(orderList)

        self.targetBalance['up'][ticker] += qty
        self.targetBalance['sp'][ticker] -= qty
        self.remainNotional -= qty * price
        self.buyingTickers.append(ticker)

    def isBuyingFinished(self):
        # 탈출조건
        '''
        remain notional이 다 소진되었는데,
        실제 balace의 notional과
        타겟 balace의 notional이 오차범위 내에 있으면 탈출
        '''
        if self.remainNotional > UPBIT_TOL_KRW:  # Decimal vs int는 가능
            return False

        upNotional = Decimal()
        ftNotional = Decimal()
        upTarget = Decimal()
        ftTarget = Decimal()
        for ticker in self.buyingTickers:
            upAsk = toDecimal(self.orderBooks['up'][tickerToUpbitSymbol(ticker)]['ask'][0][0])
            ftBid = Decimal(self.orderBooks['ft'][tickerToBnSymbol(ticker)]['bid'][0][0])
            upNotional += Decimal(self.balances['up'][ticker]) * upAsk
            upTarget += self.targetBalance['up'][ticker] * upAsk
            ftNotional += self.balances['ft'][ticker] * ftBid
            ftTarget += self.targetBalance['ft'][ticker] * ftBid

        upDiff = upTarget - upNotional
        ftDiff = ftTarget - ftNotional

        if upDiff < UPBIT_TOL_KRW and ftDiff < BINAN_TOL_USD:
            return True
        else:
            return False

    def initTransferring(self):
        self.runState = TransferState.TRANSFERRING

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
    transferMoney.startTransfer(dir=TransferDir.UpToBn, notional=1000000)

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
