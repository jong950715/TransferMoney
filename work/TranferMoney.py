import asyncio
from collections import defaultdict
from enum import Enum

from common.SingleTonAsyncInit import SingleTonAsyncInit
from common.createTask import createTask
from data.MyDataManager import MyDataManager


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
    async def _asyncInit(self, dataManager: MyDataManager):
        self.dataManger = dataManager

        self.runState = TransferState.PREPARING

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
        self.dir = dir
        self.totalNotional = notional
        self.remainNotional = notional
        self.runState = TransferState.BUYING
        self.includedTickers = []
        self.upTargetBalance = defaultdict(lambda: 0.0)
        self.ftTargetBalance = defaultdict(lambda: 0.0)

    async def runBuying(self):
        # data[i] = MyList
        # KEYS1 = ['ticker', '_price', 'price', 'volume', 'upAsk', 'spBid', 'ftBid', 'upWithdraw', 'bnDeposit']
        # KEYS2 = ['ticker', '_price', 'price', 'volume', 'upBid', 'spAsk', 'ftAsk', 'bnWithdraw', 'upDeposit']
        if self.remainNotional < 6000:
            pass #쮀낏

        data = await self.dataManger.getUpToBnData(includedTickers=[])
        data = data[0]

        ticker = data['ticker']
        price = data['upAsk']
        notional = data['volume'] * data['upAsk']

        if notional < self.remainNotional:
            qty = data['volume']
        else:
            qty = self.remainNotional / data['upAsk']

        self.order(ticker, price, qty)
        self.upTargetBalance[ticker] += qty
        self.ftTargetBalance[ticker] -= qty

        self.remainNotional -= qty * price
        
        # 탈출조건
        '''
        remain notional이 다 소진되었는데,
        실제 balace의 notional과
        타겟 balace의 notional이 오차범위 내에 있으면 탈출
        '''

    async def traceTargetBalance(self):
        while self.runState == TransferState.BUYING or self.runState == TransferState.SELLING:
            await asyncio.sleep(2)




    async def runTransferring(self):
        pass

    async def runSelling(self):
        pass

    async def runDone(self):
        pass

    def getState(self):
        return self.runState
