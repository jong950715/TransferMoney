import asyncio
from decimal import Decimal

from common.SingleTonAsyncInit import SingleTonAsyncInit
from definitions import getRootDir
from selfLib.UpClient import UpClient
from binance import AsyncClient as BnClient

from selfLib.aiopyupbit import UpbitError
from ui.MyLogger import MyLogger
from work.CheckPointManager import CheckPointManager
from work.Withdraw import Withdraw, NoToAddressError

WM_PICKLE_FILE = '{0}/work/zWalletManager.pickle'.format(getRootDir())


class WalletManager(SingleTonAsyncInit, CheckPointManager):
    async def _asyncInit(self, upCli: UpClient, bnCli: BnClient, walletInfos):
        self.upCli = upCli
        self.bnCli = bnCli

        Withdraw.initClass(upCli, bnCli, walletInfos)

        self.submittedList = []  # [[ex, id]]

        self._initPickle(WM_PICKLE_FILE,
                         ['submittedList'])

    async def submitWithdrawBatch(self, withdraws):
        tasks = [asyncio.create_task(self.submitWithdraw(*w)) for w in withdraws]
        returns, pending = await asyncio.wait(tasks)
        return returns

    async def submitWithdraw(self, fromEx, ticker, qty: Decimal):
        w = Withdraw(fromEx, ticker, qty)
        wId = await w.do()
        if wId:
            self.submittedList.append([fromEx, ticker, wId])
        self.saveCheckPoint()
        return [fromEx, ticker, wId]

    async def isAllCompleted(self):
        self.upWithdraws = await self.upCli.get_withdraw_orders()
        self.bnWithdraws = await self.bnCli.get_withdraw_history()

        for (fromEx, ticker, wId) in self.submittedList:
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

    def done(self):
        self.saveGoodExitPoint()