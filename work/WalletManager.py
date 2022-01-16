import asyncio
from datetime import datetime
from decimal import Decimal

from common.SingleTonAsyncInit import SingleTonAsyncInit
from config.MyConfigManager import MyConfigManager
from data.dataCommons import symbolToTicker, toDecimal, tickerToSymbol
from definitions import getRootDir
from selfLib.UpClient import UpClient
from binance import AsyncClient as BnClient

from selfLib.aiopyupbit import UpbitError
from ui.MyLogger import MyLogger
from work.CheckPointManager import CheckPointManager
from work.Withdraw import Withdraw, NoToAddressError

WM_PICKLE_FILE = '{0}/work/zWalletManager.pickle'.format(getRootDir())


class WalletManager(SingleTonAsyncInit, CheckPointManager):
    async def _asyncInit(self, upCli: UpClient, bnCli: BnClient, dataManager):
        self.upCli = upCli
        self.bnCli = bnCli
        self.dataManager = dataManager

        if dataManager:
            Withdraw.initClass(upCli, bnCli, dataManager.getWalletInfo())

        self.submittedList = []  # [['up', res['uuid'], self.ticker, self.qty]]

        self._initPickle(WM_PICKLE_FILE,
                         ['submittedList'])

    async def submitWithdrawBatch(self, withdraws):
        tasks = [asyncio.create_task(self.submitWithdraw(*w)) for w in withdraws]
        returns, pending = await asyncio.wait(tasks)
        return returns

    async def submitWithdraw(self, fromEx, ticker, qty: Decimal):
        w = Withdraw(fromEx, ticker, qty)
        submitted = await w.do()  # ['up', res['uuid'], self.ticker, self.qty]
        if submitted:
            MyLogger.getLogger().info('{0}에서 {1}의 {2}개 출금요청이 제출되었습니다.'.format(fromEx, ticker, qty))
            self.submittedList.append(submitted)
        self.saveCheckPoint()
        return submitted

    async def isAllCompleted(self):
        self.upWithdraws = await self.upCli.get_withdraw_orders()
        self.bnWithdraws = await self.bnCli.get_withdraw_history()

        for (fromEx, wId, ticker, qty) in self.submittedList:
            if fromEx == 'up':
                isFin = self._isFinishedUpId(wId)
            elif fromEx == 'bn':
                isFin = self._isFinishedBnId(wId)
            else:
                raise Exception('submittedList가 잘몬됨', self.submittedList)

            if isFin:
                pass
            else:
                return False

        self.done()
        return True

    def _isFinishedUpId(self, wId):
        for w in self.upWithdraws:
            if wId == w['uuid']:
                return self._upState(w['state'])
        else:
            raise Exception('uuid를 찾을 수 없습니다.')

    def _upState(self, state):
        state = state.lower()
        if state == 'done':
            return True
        elif state == 'submitting' or state == 'submitted' or state == 'almost_accepted' or state == 'accepted' or state == 'processing':
            return False
        elif state == 'rejected' or state == 'canceled':
            raise Exception('출금이 거절되었습니다. 확인해주세요.')

    def _isFinishedBnId(self, wId):
        for w in self.bnWithdraws:
            if wId == w['id']:
                return self._bnState(w['status'])
        else:
            raise Exception('id를 찾을 수 없습니다.')

    def _bnState(self, state):
        if state == 6:
            return True
        elif state == 0 or state == 2 or state == 4:
            return False
        elif state == 1 or state == 3 or state == 5:
            raise Exception('출금이 거절되었습니다. 확인해주세요.')

        '''
        0:Email Sent
        2:Awaiting Approval
        4:Processing
        
        6:Completed
        
        1:Cancelled
        3:Rejected
        5:Failure
        '''

    def getSubmittedList(self):
        return self.submittedList

    def done(self):
        self.saveGoodExitPoint()

    async def logReceipt(self, fromTime, tickers):
        krw = 0
        usdt = 0

        for ticker in tickers:
            res = await self.bnCli.get_all_orders(symbol=tickerToSymbol('bn', ticker))
            for r in res[::-1]:
                if int(r['time']) // 1000 < fromTime:
                    break
                q = toDecimal(r['executedQty'])
                p = toDecimal(r['price'])

                if r['side'] == 'BUY':
                    q = -q
                elif r['side'] == 'SELL':
                    pass
                else:
                    raise Exception('코드 잘못 짜신듯^^')

                _usdt = p * q
                _usdt -= abs(_usdt) * Decimal('0.001')
                usdt += _usdt

        for ticker in tickers:
            res = await self.bnCli.futures_get_all_orders(symbol=tickerToSymbol('bn', ticker))
            for r in res[::-1]:
                if int(r['time']) // 1000 < fromTime:
                    break
                q = toDecimal(r['executedQty'])
                p = toDecimal(r['avgPrice'])

                if r['side'] == 'BUY':
                    q = -q
                elif r['side'] == 'SELL':
                    pass
                else:
                    raise Exception('코드 잘못 짜신듯^^')

                _usdt = p * q
                _usdt -= abs(_usdt) * Decimal('0.0004')
                usdt += _usdt

        upReceipts = [await self.upCli.get_order(states=['done']),
                      await self.upCli.get_order(states=['cancel']),
                      await self.upCli.get_order(states=['wait']),
                      await self.upCli.get_order(states=['watch'])]

        upRes = []
        for receipt in upReceipts:
            for r in receipt:
                t = datetime.strptime(r['created_at'], "%Y-%m-%dT%H:%M:%S%z").timestamp()
                if t < fromTime:
                    break
                if symbolToTicker('up', r['market']) not in tickers:
                    continue
                upRes.append(r)

        for r in upRes:
            qty = toDecimal(r['executed_volume'])
            fee = toDecimal(r['paid_fee'])
            if r['side'] == 'ask':
                pass
            elif r['side'] == 'bid':
                qty = -qty
            else:
                raise Exception('코드 잘못짜신듯')

            krw += qty * toDecimal(r['price']) - fee

        MyLogger.getLogger().info('usdt : {0}'.format(usdt))
        MyLogger.getLogger().info('krw : {0}'.format(krw))
        MyLogger.getLogger().info('krw/usdt : {0}'.format(krw / usdt))

    async def issueDepositAddress(self, ticker):
        await self.upCli.generate_coin_address(ticker=ticker)
        await asyncio.sleep(5)
        await self.dataManager.exInfoManager.updateUpbitAddress()


# WalletManager

async def example():
    fromTime = datetime.strptime('2022-01-16T10:00:00+09:00', "%Y-%m-%dT%H:%M:%S%z").timestamp()

    myLogger = await MyLogger.createIns()

    await MyConfigManager.getIns()
    configKeys = MyConfigManager.getInsSync().getConfig('configKeys')

    upCli = UpClient(access=configKeys['upbit']['api_key'], secret=configKeys['upbit']['secret_key'])
    bnCli = await BnClient.create(configKeys['binance']['api_key'], configKeys['binance']['secret_key'])

    wm = await WalletManager.getIns(upCli, bnCli, None)

    await wm.logReceipt(fromTime, ['EOS', 'ZIL', 'LTC', 'ATOM'])


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(example())
