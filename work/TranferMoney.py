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
            self.initBuying(_dir, notional)

    def initBuying(self, _dir, notional):
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
        # 방향 반응형으로 만들고, GUI까지 테스트 고고하자, 피클링까지 고민해야됨..
        await self.traceTargetBalance()  # 별도로 백그라운드로 뺄 수도 있음
        await self._runBuying()
        await asyncio.sleep(3)

        if self.isBuyingFinished():
            MyLogger.getLogger().info('매수가 완료되었습니다. 매수목록: {0}'.format(self.tickers))
            MyLogger.getLogger().info('출금을 시작합니다.')
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
                raise Exception('state가 이상해..', self.runState)
        elif self._dir == TransferDir.BnToUp:
            if self.runState == TransferState.BUYING:
                buyEx = 'sp'
                sellEx = 'ft'
            elif self.runState == TransferState.SELLING:
                buyEx = 'ft'
                sellEx = 'up'
            else:
                raise Exception('state가 이상해..', self.runState)
        else:
            raise Exception('dir이 이상해..', self._dir)

        return buyEx, sellEx

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
            fromTolNotional = UPBIT_SMALL_KRW
            buyEx = 'up'
            sellEx = 'ft'
        elif self._dir == TransferDir.BnToUp:
            fromTolNotional = BINAN_SMALL_USD
            buyEx = 'sp'
            sellEx = 'ft'
        else:
            raise Exception('dir이 이상해..', self._dir)

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
        MyLogger.getLogger().info('{0}이(가) {1}개({2} 어치) 추가되었습니다. 남은양 {3}'.format(ticker, qty, qty*buyPrice, self.remainNotional))

    def _getSmallNotional(self, ex):
        if ex == 'up':
            return UPBIT_SMALL_KRW
        elif ex == 'sp' or ex == 'ft':
            return BINAN_SMALL_USD

    def isBuyingFinished(self):
        # 탈출조건
        """
        remain notional이 다 소진되었는데,
        실제 balace의 notional과
        타겟 balace의 notional이 오차범위 내에 있으면 탈출
        """
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
            raise Exception('dir이 이상해..', self._dir)

        if self.remainNotional > buyTolNotional:  # Decimal vs int는 가능
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
        MyLogger.getLogger().info('출금요청이 모두 완료되었습니다. 입금 대기 하겠습니다.')
        await self.waitForTransferred()
        MyLogger.getLogger().info('입금이 확인되었습니다.')
        await self.initSelling()
        """
            해야할 일
            돈 안보냈으면 보내고
                - 지갑 밸리데이트 하고
                - 업비트에 지갑 등록 안되어 있으면 하고 (등록해달라고 로그 띄우고)
                - 돈 도착했는지 확인하고 (uuid랑 도착지 balance)

            단계로 나눠 보면
                - 돈 보내기 단계
                    - 지갑 주소 검증
                    - 출금
                        - 최소 출금량
                        - 최대 출금량
                        - 수수료 고려 등
                    - 에러나면?
                        - 지갑 등록 해주세요 에러나면 메시지 띄우고 좀 쉬기

                - 돈 보내지기 기다리기 단계
                    - status 확인
                    - balance 확인

                - 그럼 끗
        """

    async def _runTransferring(self):
        if self._dir == TransferDir.UpToBn:
            fromEx = 'up'
            buyEx = 'up'
        elif self._dir == TransferDir.BnToUp:
            fromEx = 'bn'
            buyEx = 'sp'
        else:
            raise Exception('이상', self._dir)

        await self.dataManager.updateBalances(tickers=self.tickers)

        withdraws = []
        # 출금 목록 만들기
        for ticker in self.tickers:
            qty = toDecimal(self.balances[buyEx][ticker])
            withdraws.append([fromEx, ticker, qty])

        MyLogger.getLogger().info('len(withdraws) = {0}'.format(len(withdraws)))

        # 제출하기
        rets = await self.walletManager.submitWithdrawBatch(withdraws)

        isRecursion = False
        waitTime = 0

        for ret in rets:
            try:
                await ret
                ret.result()  # [fromEx, ticker, wId]
                continue  # 잘 되었으면 탈출
            except UpbitError as e:
                if e.name == 'withdraw_address_not_registered':
                    MyLogger.getLogger().info('{0}의 업비트 출금주소를 등록해주세요.'.format(e.ticker))
                    isRecursion = True
                    waitTime = 60 if waitTime < 60 else waitTime

                elif e.name == 'withdraw_insufficient_balance' or e.name == 'withdraw_decimal_places_exceeded':
                    raise Exception('로직 오류가 의심 됩니다.', e, e.ticker)

            except NoToAddressError as e:
                MyLogger.getLogger().info('{0} 거래소의 {1} 입금주소가 존재하지 않습니다. '
                                          '발급 받고 있습니다.'.format(e.ex, e.ticker))
                await self.walletManager.issueDepositAddress(e.ticker)
                isRecursion = True
                waitTime = 60 if waitTime < 60 else waitTime

            except Exception as e:
                raise e

        MyLogger.getLogger().info('len(rets) = {0}'.format(len(rets)))

        if isRecursion:
            await asyncio.sleep(waitTime)
            await self._runTransferring()  #재도즈언

    async def waitForTransferred(self):
        isFin = await self.walletManager.isAllCompleted()
        while not isFin:
            isFin = await self.walletManager.isAllCompleted()
            await asyncio.sleep(10)

        MyLogger.getLogger().info('출금 거래소의 처리가 끝났습니다. 입금 거래소의 입금을 기다리겠습니다.')

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
            raise Exception('문제있다.', self._dir)

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
        MyLogger.getLogger().info('매도를 시작하겠습니다.')
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
            MyLogger.getLogger().info('매도가 완료되었습니다.')
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
            raise Exception('ex이상', sellEx)

        for ticker in self.tickers:
            tb = self.targetBalances[sellEx][ticker]
            tb -= maxOneNotional
            tb = 0 if tb < smallNotional else tb
            self.targetBalances[sellEx][ticker] = tb
            self.targetBalances[buyEx][ticker] = tb

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
        MyLogger.getLogger().info('끝!')
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
