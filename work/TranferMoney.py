import asyncio
import re
from collections import defaultdict
from decimal import Decimal
from enum import Enum
from datetime import datetime

from common.SingleTonAsyncInit import SingleTonAsyncInit
from common.createTask import createTask
from data.MyDataManager import MyDataManager
from data.dataCommons import toDecimal, tickerToSymbol
from definitions import getRootDir
from selfLib.UpClient import UpClient
from binance import AsyncClient as BnClient
from selfLib.aiopyupbit import UpbitError
from ui.MyLogger import MyLogger
from work.CheckPointManager import CheckPointManager
from work.Enums import TransferState, TransferDir
from work.OrderManager import OrderManager
from work.WalletManager import WalletManager
from work.Withdraw import NoToAddressError

UPBIT_SMALL_KRW = Decimal(30000)
BINAN_SMALL_USD = Decimal(30)

TM_PICKLE_FILE = '{0}/work/zTransferMoney.pickle'.format(getRootDir())


class TransferMoney(SingleTonAsyncInit, CheckPointManager):
    async def _asyncInit(self, dataManager: MyDataManager, upCli: UpClient, bnCli: BnClient):
        self.dataManager = dataManager

        self.orderManager = await OrderManager.createIns(upCli=upCli, bnCli=bnCli, exInfo=dataManager.getExInfo())
        self.walletManager = await WalletManager.createIns(upCli=upCli, bnCli=bnCli,
                                                           dataManager=dataManager)

        self.runState = TransferState.PREPARING

        self.orderBooks = dataManager.getOrderBooks()
        self.balances = dataManager.getBalances()
        # self.walletInfo = self.dataManager.getWalletInfo()

        self._initPickle(TM_PICKLE_FILE,
                         ['_dir', 'totalNotional', 'remainNotional', 'tickers', 'targetBalances', 'runState',
                          'startTime'])

        self.run()

    def run(self):
        if self.startTime:
            pass
        else:
            self.startTime = int(datetime.now().timestamp())  # in seconds
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
        if self.dataManager:
            self.runState = TransferState.STANDBY

    async def runStandby(self):
        pass

    def startTransfer(self, _dir: TransferDir, notional):
        if self.runState == TransferState.STANDBY:
            asyncio.get_event_loop().call_soon(asyncio.create_task, self.initBuying(_dir, notional))

    async def validateBalance(self, _dir, notional):
        await self.dataManager.updateBalances([])
        if _dir == TransferDir.UpToBn:
            return (notional < self._getBalance('up', 'KRW')) and (
                        (notional / Decimal('1200') * Decimal('0.2')) < self._getBalance('ft', 'USDT'))
        elif _dir == TransferDir.BnToUp:
            return (notional < self._getBalance('sp', 'USDT')) and (
                    (notional * Decimal('0.2')) < self._getBalance('ft', 'USDT'))

    async def initBuying(self, _dir, notional):
        if (await self.validateBalance(_dir, notional)):
            MyLogger.getLogger().info('????????? ???????????????.')
        else:
            MyLogger.getLogger().info('?????? ???????????????. ????????? ??????????????????.')
            return
        self._dir = _dir

        self.totalNotional = notional
        self.remainNotional = notional

        self.tickers = set()

        self.targetBalances = {'up': defaultdict(Decimal),
                               'sp': defaultdict(Decimal),
                               'ft': defaultdict(Decimal)
                               }

        self.runState = TransferState.BUYING

        self.saveCheckPoint()

    async def runBuying(self):
        # ?????? ??????????????? ?????????, GUI?????? ????????? ????????????, ??????????????? ???????????????..
        await self.traceTargetBalance()  # ????????? ?????????????????? ??? ?????? ??????
        await self._runBuying()
        await asyncio.sleep(3)

        if self.isBuyingFinished():
            MyLogger.getLogger().info('????????? ?????????????????????. ????????????: {0}'.format(self.tickers))
            MyLogger.getLogger().info('????????? ???????????????.')
            self.initTransferring()
            self.orderManager.done()

    async def cancelAllOrders(self):
        await self.orderManager.cancelOrderBatch()

    def getBuySellEx(self):
        if self._dir == TransferDir.UpToBn:
            if self.runState == TransferState.BUYING:
                buyEx = 'up'
                sellEx = 'ft'
            elif self.runState == TransferState.SELLING:
                buyEx = 'ft'
                sellEx = 'sp'
            else:
                raise Exception('state??? ?????????..', self.runState)
        elif self._dir == TransferDir.BnToUp:
            if self.runState == TransferState.BUYING:
                buyEx = 'sp'
                sellEx = 'ft'
            elif self.runState == TransferState.SELLING:
                buyEx = 'ft'
                sellEx = 'up'
            else:
                raise Exception('state??? ?????????..', self.runState)
        else:
            raise Exception('dir??? ?????????..', self._dir)

        return buyEx, sellEx

    async def traceTargetBalance(self):
        """
        ????????? ??????
        self.dir
        self.totalNotional
        self.remainNotional
        self.buyingTickers
        self.targetBalances
        self.runState

        ????????? ??????
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
        buyEx, sellEx = self.getBuySellEx()

        await self.cancelAllOrders()
        await self.dataManager.updateBalances(tickers=self.tickers)

        orderList = []
        for ticker in self.tickers:
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
        elif ex == 'sp' or ex == 'ft' or ex == 'bn':
            return self.balances[ex][ticker]

    def _getBestBidAskPrice(self, ex, sym, bidAsk):
        return toDecimal(self.orderBooks[ex][sym][bidAsk][0][0])
        # if ex == 'up':
        #     return Decimal(self.orderBooks[ex][sym][bidAsk][0][0])
        # elif ex == 'sp' or ex == 'ft':
        #     return toDecimal(self.orderBooks[ex][sym][bidAsk][0][0])

    async def _runBuying(self):
        """
        ?????????
        UPBIT_TOL_KRW
        sym
        price
        notional
        qty
        ftSym
        ftPrice
        """
        if self._dir == TransferDir.UpToBn:
            fromTolNotional = UPBIT_SMALL_KRW
            buyEx = 'up'
            sellEx = 'ft'
        elif self._dir == TransferDir.BnToUp:
            fromTolNotional = BINAN_SMALL_USD
            buyEx = 'sp'
            sellEx = 'ft'
        else:
            raise Exception('dir??? ?????????..', self._dir)

        if self.remainNotional < fromTolNotional:
            return

        # data[i] = MyList
        # KEYS1 = ['ticker', '_price', 'price', 'volume', 'upAsk', 'spBid', 'ftBid', 'upWithdraw', 'bnDeposit']
        # KEYS2 = ['ticker', '_price', 'price', 'volume', 'upBid', 'spAsk', 'ftBid', 'bnWithdraw', 'upDeposit']

        data = await self.dataManager.getDataByDir(_dir=self._dir, includedTickers=self.tickers,
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
        self.tickers.add(ticker)
        self.saveCheckPoint()
        MyLogger.getLogger().info(
            '{0}???(???) {1}???({2} ??????) ?????????????????????. ????????? {3}'.format(ticker, qty, qty * buyPrice, self.remainNotional))

    def _getSmallNotional(self, ex):
        if ex == 'up':
            return UPBIT_SMALL_KRW
        elif ex == 'sp' or ex == 'ft':
            return BINAN_SMALL_USD

    def isBuyingFinished(self):
        # ????????????
        """
        remain notional??? ??? ??????????????????,
        ?????? balace??? notional???
        ?????? balace??? notional??? ???????????? ?????? ????????? ??????
        """
        """
        ????????? ??????
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
            buyTolNotional = UPBIT_SMALL_KRW
            sellTolNotional = BINAN_SMALL_USD
            buyEx = 'up'
            sellEx = 'ft'
        elif self._dir == TransferDir.BnToUp:
            buyTolNotional = BINAN_SMALL_USD
            sellTolNotional = BINAN_SMALL_USD
            buyEx = 'sp'
            sellEx = 'ft'
        else:
            raise Exception('dir??? ?????????..', self._dir)

        if self.remainNotional > buyTolNotional:  # Decimal vs int??? ??????
            return False

        buyNotional = Decimal()
        sellNotional = Decimal()
        buyTargetNotional = Decimal()
        sellTargetNotional = Decimal()
        for ticker in self.tickers:
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
        # self.withdraws = []
        self.saveCheckPoint()

    async def runTransferring(self):
        await self._runTransferring()
        MyLogger.getLogger().info('??????????????? ?????? ?????????????????????. ?????? ?????? ???????????????.')
        await self.waitForTransferred()
        MyLogger.getLogger().info('????????? ?????????????????????.')
        await self.initSelling()
        """
            ????????? ???
            ??? ??????????????? ?????????
                - ?????? ??????????????? ??????
                - ???????????? ?????? ?????? ????????? ????????? ?????? (?????????????????? ?????? ?????????)
                - ??? ??????????????? ???????????? (uuid??? ????????? balance)

            ????????? ?????? ??????
                - ??? ????????? ??????
                    - ?????? ?????? ??????
                    - ??????
                        - ?????? ?????????
                        - ?????? ?????????
                        - ????????? ?????? ???
                    - ?????????????
                        - ?????? ?????? ???????????? ???????????? ????????? ????????? ??? ??????

                - ??? ???????????? ???????????? ??????
                    - status ??????
                    - balance ??????

                - ?????? ???
        """

    async def _runTransferring(self):
        if self._dir == TransferDir.UpToBn:
            fromEx = 'up'
            buyEx = 'up'
        elif self._dir == TransferDir.BnToUp:
            fromEx = 'bn'
            buyEx = 'sp'
        else:
            raise Exception('??????', self._dir)

        await self.dataManager.updateBalances(tickers=self.tickers)

        withdraws = []
        # ?????? ?????? ?????????
        for ticker in self.tickers:
            qty = toDecimal(self.balances[buyEx][ticker])
            withdraws.append([fromEx, ticker, qty])

        # ????????????
        rets = await self.walletManager.submitWithdrawBatch(withdraws)

        isRecursion = False
        waitTime = 0

        for ret in rets:
            try:
                await ret
                ret.result()  # [fromEx, ticker, wId]
                continue  # ??????????????? ??????
            except UpbitError as e:
                if e.name == 'withdraw_address_not_registered':
                    MyLogger.getLogger().info('{0}??? ????????? ??????????????? ??????????????????.'.format(e.ticker))
                    isRecursion = True
                    waitTime = 60 if waitTime < 60 else waitTime

                elif e.name == 'withdraw_insufficient_balance' or e.name == 'withdraw_decimal_places_exceeded':
                    raise Exception('?????? ????????? ?????? ?????????.', e, e.ticker)

            except NoToAddressError as e:
                MyLogger.getLogger().info('{0} ???????????? {1} ??????????????? ???????????? ????????????. '
                                          '?????? ?????? ????????????.'.format(e.ex, e.ticker))
                await self.walletManager.issueDepositAddress(e.ticker)
                isRecursion = True
                waitTime = 60 if waitTime < 60 else waitTime

            except Exception as e:
                raise e

        # Task exception was never retrieved ????????? ?????? ??? ?????? flag ????????? recursion ???????????????
        if isRecursion:
            await asyncio.sleep(waitTime)
            await self._runTransferring()  # ????????????

    async def waitForTransferred(self):
        isFin = await self.walletManager.isAllCompleted()
        while not isFin:
            isFin = await self.walletManager.isAllCompleted()
            await asyncio.sleep(10)

        MyLogger.getLogger().info('?????? ???????????? ????????? ???????????????. ?????? ???????????? ????????? ?????????????????????.')

        # (fromEx, wId, ticker, qty)
        withdrawList = self.walletManager.getSubmittedList()

        withdrawQty = defaultdict(Decimal)
        for (fromEx, wId, ticker, qty) in withdrawList:
            withdrawQty[ticker] += qty

        if self._dir == TransferDir.UpToBn:
            ex = 'sp'
        elif self._dir == TransferDir.BnToUp:
            ex = 'up'
        else:
            raise Exception('????????????.', self._dir)

        while True:
            await self.dataManager.updateBalances(tickers=self.tickers)
            for ticker in self.tickers:
                bal = self._getBalance(ex, ticker)
                wit = withdrawQty[ticker]

                if bal < wit * Decimal(0.95):
                    await asyncio.sleep(5)
                    break
            else:
                break

    async def initSelling(self):
        MyLogger.getLogger().info('????????? ?????????????????????.')
        self.runState = TransferState.SELLING
        self.targetBalances = {'up': defaultdict(Decimal),
                               'sp': defaultdict(Decimal),
                               'ft': defaultdict(Decimal)
                               }

        await self.dataManager.updateBalances(tickers=self.tickers)

        orderList = []
        for ticker in self.tickers:
            upBalanceQty = self._getBalance('up', ticker)
            spBalanceQty = self._getBalance('sp', ticker)
            ftBalanceQty = self._getBalance('ft', ticker)

            self.targetBalances['up'][ticker] = upBalanceQty
            self.targetBalances['sp'][ticker] = spBalanceQty
            self.targetBalances['ft'][ticker] = ftBalanceQty

        self.saveCheckPoint()

    async def runSelling(self):
        await self._runSelling()
        await self.traceTargetBalance()
        await asyncio.sleep(3)

        if self.isSellingFinished():
            MyLogger.getLogger().info('????????? ?????????????????????.')
            await self.initDone()

    async def _runSelling(self):
        buyEx, sellEx = self.getBuySellEx()

        if sellEx == 'sp':
            maxOneNotional = 3000
            smallNotional = BINAN_SMALL_USD
        elif sellEx == 'up':
            maxOneNotional = 3000000
            smallNotional = UPBIT_SMALL_KRW
        else:
            raise Exception('ex??????', sellEx)

        for ticker in self.tickers:
            sellPrice = self._getBestBidAskPrice(sellEx, tickerToSymbol(sellEx, ticker), 'bid')
            maxOneQty = maxOneNotional/sellPrice
            tb = self.targetBalances[sellEx][ticker]
            tb -= maxOneQty # ERROR
            tb = 0 if tb < smallNotional else tb
            self.targetBalances[sellEx][ticker] = tb
            self.targetBalances[buyEx][ticker] = -tb

        self.saveCheckPoint()

    def isSellingFinished(self):
        buyEx, sellEx = self.getBuySellEx()
        sellSmall = self._getSmallNotional(sellEx)
        buySmall = self._getSmallNotional(buyEx)

        for ticker in self.tickers:
            sellTarget = self.targetBalances[sellEx][ticker]
            buyTarget = self.targetBalances[buyEx][ticker]

            sellBal = self._getBalance(sellEx, ticker)
            buyBal = self._getBalance(buyEx, ticker)

            if (abs(buyTarget - buyBal) > buySmall) or (abs(sellTarget - sellBal) > sellSmall):
                return False
        else:
            return True

        raise Exception('unreachable')

    async def initDone(self):
        MyLogger.getLogger().info('???!')
        self.runState = TransferState.DONE
        await self.walletManager.logReceipt(self.startTime, self.tickers)
        self.saveCheckPoint()

    async def runDone(self):
        await self.walletManager.logReceipt(self.startTime, self.tickers)
        await asyncio.sleep(10)

    # self.startTime

    def getState(self):
        return self.runState


async def main():
    dataManager = await MyDataManager.createIns()
    transferMoney = await TransferMoney.createIns(dataManager)
    transferMoney.startTransfer(_dir=TransferDir.UpToBn, notional=1000000)

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
