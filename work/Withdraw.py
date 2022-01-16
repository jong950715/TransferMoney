import asyncio
import re
from decimal import Decimal
from datetime import datetime

from config.MyConfigManager import MyConfigManager
from selfLib.UpClient import UpClient
from binance import AsyncClient as BnClient

from selfLib.aiopyupbit import UpbitError


class NoToAddressError(Exception):
    def __init__(self, ex, ticker):
        self.ex = ex
        self.ticker = ticker


class Withdraw:
    upCli = None
    bnCli = None
    walletInfos = None

    @classmethod
    def initClass(cls, upCli: UpClient, bnCli: BnClient, walletInfos):
        cls.upCli = upCli
        cls.bnCli = bnCli
        cls.walletInfos = walletInfos

    def __init__(self, fromEx, ticker, qty: Decimal):
        self.skip = False
        self.ticker = ticker
        self.qty = qty
        self.fromEx = fromEx
        if fromEx == 'up':
            self.toEx = 'bn'
        elif fromEx == 'bn':
            self.toEx = 'up'
        else:
            raise Exception('등록되지 않은 거래소', fromEx)

        self.upCli = self.__class__.upCli
        self.bnCli = self.__class__.bnCli
        self.walletInfos = self.__class__.walletInfos

        self.loadInfos()
        self.validateParams()

    def loadInfos(self):
        self.minQty = self.walletInfos[self.fromEx][self.ticker]['withdrawMin']
        self.maxQty = self.walletInfos[self.fromEx][self.ticker]['withdrawMax']
        self.qtyStep = self.walletInfos[self.fromEx][self.ticker]['withdrawDecimal']
        if self.ticker == 'NEO':
            self.qtyStep = Decimal('1')
        self.fee = self.walletInfos[self.fromEx][self.ticker]['fee']

        try:
            self.addr1 = self.walletInfos[self.toEx][self.ticker]['address1']
            self.addr2 = self.walletInfos[self.toEx][self.ticker]['address2']
        except KeyError as e:
            if self.toEx == 'up':
                raise NoToAddressError(self.toEx, self.ticker)
            raise Exception(self.toEx, self.ticker, e)
        except Exception as e:
            raise e

    async def do(self):
        if self.skip:
            return None
        if self.fromEx == 'up':
            return await self._upWithdraw()
        elif self.fromEx == 'bn':
            return await self._bnWithdraw()
        raise Exception('거래소 오류', self.fromEx)

    def validateParams(self):
        """
        최대값, 최소값, step, address, 수수료
        """
        if self.fromEx == 'up':
            self.qty -= self.fee

        self.qty = (self.qty // self.qtyStep) * self.qtyStep

        if self.qty < self.minQty:
            self.skip = True
        if self.maxQty < self.qty:
            raise Exception('최대전송 수량: {0}, 전송요청 수량: {1}'.format(self.maxQty, self.qty))

        if re.match(self.walletInfos['bn'][self.ticker]['regex'], self.addr1):
            return True
        else:
            raise Exception('입금주소가 이상합니다.', self.addr1)

    async def _upWithdraw(self):
        try:
            res = await self.upCli.withdraw_coin(currency=self.ticker, amount=self.qty, address=self.addr1,
                                                 secondary_address=self.addr2)
        except UpbitError as e:
            e.setTicker(self.ticker)
            raise e
        except Exception as e:
            raise e

        return ['up', res['uuid'], self.ticker, self.qty]  # 수수료 적용된 qty임!!

    async def _bnWithdraw(self):
        res = await self.bnCli.withdraw(coin=self.ticker, address=self.addr1,
                                        addressTag=self.addr2, amount=self.qty)
        return ['bn', res['id'], self.ticker, self.qty-self.fee]


async def example():
    await MyConfigManager.getIns()
    configKeys = MyConfigManager.getInsSync().getConfig('configKeys')

    upCli = UpClient(access=configKeys['upbit']['api_key'], secret=configKeys['upbit']['secret_key'])
    bnCli = await BnClient.create(configKeys['binance']['api_key'], configKeys['binance']['secret_key'])

    # ticker = 'EOS'
    # qty = Decimal('0.2')
    #
    # res = await upCli.get_order(states=['done'])
    # print(res)
    #
    # start = datetime.strptime('2022-01-13T20:50:28+09:00', "%Y-%m-%dT%H:%M:%S%z").timestamp()
    # _res = []
    # for r in res:
    #     t = datetime.strptime(r['created_at'], "%Y-%m-%dT%H:%M:%S%z").timestamp()
    #     if t < start:
    #         break
    #     _res.append(r)
    #
    # print(_res)
    #
    #
    # res['side']
    # res['executed_volume']
    # res['price']
    # res['paid_fee']
    # res['created_at'] # '2022-01-13T21:26:28+09:00'
    #
    # return
    #
    # res = await upCli.generate_coin_address(ticker=ticker)
    # print(res)
    #
    # res = await upCli.get_deposit_addresses()
    # print(res)
    # for r in res:
    #     if r['currency'] == ticker:
    #         addr1 = r['deposit_address']
    #         addr2 = r['secondary_address']
    #         break

    # res = await bnCli.withdraw(coin=ticker, address = addr1, addressTag=addr2, amount=qty, withdrawOrderId='merong378')
    # print(res['id'])

    # res = await bnCli.get_withdraw_history(withdrawOrderId = 'merong378')

    # res = await bnCli.get_withdraw_history()
    # print(res)
    #
    # res = await upCli.get_withdraw_orders()
    # print(res)

    # '62f85fd002744121bf42e8779d1a9f94'
    # '41da7636fb26486d92a734ed174254b8'

    # res = await upCli.get_withdraw_chance(ticker='SAND')
    # print(res)
    # return

    # res = await upCli.get_balances()
    # print(res)
    #
    # res = await upCli.get_individual_withdraw_order(currency='EOS', uuid='9d3982f1-e790-4600-942c-8268c3d2901e')
    # print(res)
    # print(res['state'])
    #
    # try:
    #     res = await upCli.withdraw_coin(currency='EOS', amount=Decimal('1'), address='binancecleos',
    #                                     secondary_address='100366452')
    #     print(res['uuid'])
    # except UpbitError as e:
    #     if e.name == 'withdraw_address_not_registered':
    #         pass
    #     if e.name == 'withdraw_insufficient_balance':
    #         pass
    #     if e.name == 'withdraw_decimal_places_exceeded':
    #         pass
    #     print(e.code)
    #     print(e.name)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(example())
