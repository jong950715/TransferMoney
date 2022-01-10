import asyncio
from decimal import Decimal
from binance import AsyncClient as BnClient

from config.MyConfigManager import MyConfigManager
from selfLib.UpClient import UpClient

from data.dataCommons import getUpbitPriceStep


class BaseOrder:
    cli = None
    orderInfo = None

    @classmethod
    def initClass(cls, client, orderInfo):
        cls.cli = client
        cls.orderInfo = orderInfo

    def __init__(self, sym, price: Decimal, qty: Decimal):
        # Do use decimal!
        self.sym = sym
        self.price = price
        self.qty = qty

        self.loadInfos()

    # 만들어 주세요 #
    async def submit(self):
        pass

    # 만들어 주세요 #
    def loadInfos(self):
        self.priceStep = (self.orderInfo[self.sym]['priceStep'])  # Decimal
        self.qtyStep = (self.orderInfo[self.sym]['qtyStep'])  # Decimal #upbit 다름
        self.minValue = (self.orderInfo[self.sym]['minValue'])  # Decimal

    def fitByRound(self):
        # 가격 step, 수량 step에 대해 반올림 --> 주문금액, 주문량 나옴
        # 최소 주문금액, 최소 주문량에 대해는 validate
        self.price = self.priceStep * round(self.price / self.priceStep)
        self.qty = self.qtyStep * round(self.qty / self.qtyStep)
        return self.validate()

    def validate(self):
        # 가격 step, 수량 step, 최소 주문금액, 최소 주문량
        # issue:: 주문금액, 포지션 금액 확인해서 청산비율 체크

        if self.price % self.priceStep != 0:
            message = (' =====가격 정밀도 에러====='
                       '\t sym : {0}'
                       '\t price : {1}'
                       '\t priceStep : {2}'
                       '\t =====가격 정밀도 에러=====\n '
                       .format(self.sym, self.price, self.priceStep))
            raise Exception(message)  # round를 했는데 있을 수 없는 상황 이므로 Exception

        if self.qty % self.qtyStep != 0:
            message = (' =====수량 정밀도 에러====='
                       '\t sym : {0}'
                       '\t qty : {1}'
                       '\t qtyStep : {2}'
                       '\t =====수량 정밀도 에러=====\n '
                       .format(self.sym, self.qty, self.qtyStep))
            raise Exception(message)  # round를 했는데 있을 수 없는 상황 이므로 Exception

        if abs(self.qty * self.price) < self.minValue:
            message = (' =====주문금액 작아서 에러===== '
                       '\n sym : {0} '
                       '\n qty*price : {1} '
                       '\n =====주문금액 작아서 에러=====\n'
                       .format(self.sym, self.qty * self.price))

            return False

    def logOrder(self):
        msg = (
                '#ORDER#'
                '\n sym : %s'
                '\n p : %f'
                '\n q : %f' % (self.sym, self.price, self.qty))

        print(msg)

    async def execute(self):
        # 검증
        if self.fitByRound() is False:
            return

        if self.qty:
            await self.submit()
        else:
            raise Exception("qty 0 주문은 안돼~")

        self.logOrder()


class FtOrder(BaseOrder):
    async def submit(self):
        if self.qty > 0:
            side = 'BUY'
        else:
            side = 'SELL'
            self.qty = -self.qty
        res = await self.cli.futures_create_order(symbol=self.sym, price=self.price,
                                                  quantity=self.qty, side=side,
                                                  type='LIMIT', timeInForce='GTC')


class SpOrder(BaseOrder):
    async def submit(self):
        if self.qty > 0:
            side = 'BUY'
        else:
            side = 'SELL'
            self.qty = -self.qty
        await self.cli.create_order(symbol=self.sym, price=self.price,
                                    quantity=self.qty, side=side,
                                    type='LIMIT', timeInForce='GTC')


class UpOrder(BaseOrder):
    async def submit(self):
        if self.qty > 0:
            side = 'bid'
        else:
            side = 'ask'
            self.qty = -self.qty
        await self.cli.create_limit_order(symbol=self.sym, price=self.price,
                                          quantity=self.qty, side=side)

    def loadInfos(self):
        self.priceStep = getUpbitPriceStep(self.price)
        self.qtyStep = (self.orderInfo[self.sym]['qtyStep'])  # Decimal
        self.minValue = (self.orderInfo[self.sym]['minValue'])  # Decimal


async def example():
    await MyConfigManager.getIns()
    configKeys = MyConfigManager.getInsSync().getConfig('configKeys')

    upCli = UpClient(access=configKeys['upbit']['api_key'], secret=configKeys['upbit']['secret_key'])
    bnCli = await BnClient.create(configKeys['binance']['api_key'], configKeys['binance']['secret_key'])

    await upCli.create_limit_order(symbol='KRW-BTC', price='40000000',
                                   quantity='0.01', side='bid')

    # await bnCli.create_order(symbol='BTCUSDT', price='40001',
    #                          quantity='0.01', side='BUY',
    #                          type='LIMIT', timeInForce='GTC')


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(example())
