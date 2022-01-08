from common.createTask import createTask
from selfLib.UpbitExtra import UpbitExtra
from selfLib.UpClientDecorator import *


class UpClient(UpbitExtra):
    _ORDER_PER_SEC = 8-1
    _GENERAL_PER_SEC = 30-1

    def __init__(self, *args, **kwargs):
        super(UpClient, self).__init__(*args, **kwargs)
        '''
        주문관련 초당 8회, 분당 200회
        이외 초당 30회, 분당 900회
        
        사실 분당은 안넘겠지... 가정하는것임
        
        그리고 업비트 내부적으로 1초마다 remain 업뎃하는게 확인되었음.
        '''

        self.orderRemains = self._ORDER_PER_SEC
        self.generalRemains = self._GENERAL_PER_SEC

        self.run()

    def run(self):
        asyncio.get_event_loop().call_soon(createTask, self._run())

    async def _run(self):
        while True:
            await asyncio.sleep(1.2)
            self.orderRemains += self._ORDER_PER_SEC
            self.generalRemains += self._GENERAL_PER_SEC
            self.orderRemains = self.orderRemains if self.orderRemains < self._ORDER_PER_SEC else self._ORDER_PER_SEC
            self.generalRemains = self.generalRemains if self.generalRemains < self._GENERAL_PER_SEC else self._GENERAL_PER_SEC

    @checkRemainGeneral
    async def decoratorSample1(self):
        pass

    @checkRemainOrder
    async def decoratorSample2(self):
        pass

    @checkRemainOrder
    async def buy_limit_order(self, *args, **kwargs):
        return await super(UpClient, self).buy_limit_order(*args, **kwargs)

    @checkRemainOrder
    async def buy_market_order(self, *args, **kwargs):
        return await super(UpClient, self).buy_market_order(*args, **kwargs)

    @checkRemainOrder
    async def sell_limit_order(self, *args, **kwargs):
        return await super(UpClient, self).sell_limit_order(*args, **kwargs)

    @checkRemainOrder
    async def sell_market_order(self, *args, **kwargs):
        return await super(UpClient, self).sell_market_order(*args, **kwargs)

    @checkRemainOrder
    async def cancel_order(self, *args, **kwargs):
        return await super(UpClient, self).cancel_order(*args, **kwargs)

    @checkRemainGeneral
    async def get_individual_order(self, *args, **kwargs):
        return await super(UpClient, self).get_individual_order(*args, **kwargs)

    @checkRemainGeneral
    async def get_chance(self, *args, **kwargs):
        return await super(UpClient, self).get_chance(*args, **kwargs)

    @checkRemainGeneral
    async def check_authentication(self, *args, **kwargs):
        return await super(UpClient, self).check_authentication(*args, **kwargs)

    @checkRemainGeneral
    async def get_amount(self, *args, **kwargs):
        return await super(UpClient, self).get_amount(*args, **kwargs)

    @checkRemainGeneral
    async def get_api_key_list(self, *args, **kwargs):
        return await super(UpClient, self).get_api_key_list(*args, **kwargs)

    @checkRemainGeneral
    async def get_avg_buy_price(self, *args, **kwargs):
        return await super(UpClient, self).get_avg_buy_price(*args, **kwargs)

    @checkRemainGeneral
    async def get_balance(self, *args, **kwargs):
        return await super(UpClient, self).get_balance(*args, **kwargs)

    @checkRemainGeneral
    async def get_balance_t(self, *args, **kwargs):
        return await super(UpClient, self).get_balance_t(*args, **kwargs)

    @checkRemainGeneral
    async def get_balances(self, *args, **kwargs):
        return await super(UpClient, self).get_balances(*args, **kwargs)

    @checkRemainGeneral
    async def get_deposit_addresses(self, *args, **kwargs):
        return await super(UpClient, self).get_deposit_addresses(*args, **kwargs)

    @checkRemainGeneral
    async def get_deposit_withdraw_status(self, *args, **kwargs):
        return await super(UpClient, self).get_deposit_withdraw_status(*args, **kwargs)

    @checkRemainGeneral
    async def get_individual_withdraw_order(self, *args, **kwargs):
        return await super(UpClient, self).get_individual_withdraw_order(*args, **kwargs)

    @checkRemainGeneral
    async def get_markets(self, *args, **kwargs):
        return await super(UpClient, self).get_markets(*args, **kwargs)

    @checkRemainGeneral
    async def get_order(self, *args, **kwargs):
        return await super(UpClient, self).get_order(*args, **kwargs)

    @checkRemainGeneral
    async def get_trades_ticks(self, *args, **kwargs):
        return await super(UpClient, self).get_trades_ticks(*args, **kwargs)

    @checkRemainGeneral
    async def get_withdraw_chance(self, *args, **kwargs):
        return await super(UpClient, self).get_withdraw_chance(*args, **kwargs)

    @checkRemainGeneral
    async def withdraw_cash(self, *args, **kwargs):
        return await super(UpClient, self).withdraw_cash(*args, **kwargs)

    @checkRemainGeneral
    async def withdraw_coin(self, *args, **kwargs):
        return await super(UpClient, self).withdraw_coin(*args, **kwargs)
