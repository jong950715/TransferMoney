import re

from selfLib.aiopyupbit import Upbit
from selfLib.aiopyupbit.request_api import _send_get_request, _send_post_request, _send_delete_request, _call_public_api


class UpbitExtra(Upbit):
    """
    정의 안되어있는 API들 추가 정의 하였습니다.
    """

    def __init__(self, *args, **kwargs):
        super(UpbitExtra, self).__init__(*args, **kwargs)
        '''
        주문관련 초당 8회, 분당 200회
        이외 초당 30회, 분당 900회
        '''

    async def get_withdraw_chance(self, ticker: str, contain_req: bool = False) -> tuple or list:
        try:
            url = "https://api.upbit.com/v1/withdraws/chance"
            data = {"currency": ticker}
            headers = await self._request_headers(data)
            body, remain = await _send_get_request(url, headers=headers, data=data)
            return (body, remain) if contain_req else body
        except Exception as e:
            raise e

    async def get_deposit_addresses(self, contain_req: bool = False) -> tuple or list:
        try:
            url = "https://api.upbit.com/v1/deposits/coin_addresses"
            headers = await self._request_headers()
            body, remain = await _send_get_request(url, headers=headers)
            return (body, remain) if contain_req else body
        except Exception as e:
            raise e

    async def get_markets(self, contain_req: bool = False) -> tuple or list:
        try:
            url = "https://api.upbit.com/v1/market/all"
            headers = await self._request_headers()
            body, remain = await _send_get_request(url, headers=headers)
            return (body, remain) if contain_req else body
        except Exception as e:
            raise e

    async def get_trades_ticks(self, symbol: str = "KRW-BTC") -> float or dict or tuple:
        try:
            url = "https://api.upbit.com/v1/trades/ticks"
            body, remain = await _call_public_api(url, market=symbol)
            return body[0]
        except Exception as e:
            raise e

    async def create_limit_order(self, symbol, side, price, quantity, contain_req: bool = False) -> tuple or dict:
        try:
            url = "https://api.upbit.com/v1/orders"
            data = {"market": symbol,
                    "side": side,
                    "volume": quantity,
                    "price": price,
                    "ord_type": "limit"}
            headers = await self._request_headers(data)
            body, remain = await _send_post_request(url, headers=headers, data=data)
            return (body, remain) if contain_req else body
        except Exception as e:
            raise e

    async def withdraw_coin(self,
                            currency,
                            amount,
                            address,
                            secondary_address=None,
                            transaction_type: str = 'default',
                            contain_req: bool = False) -> tuple or dict:
        try:
            url = "https://api.upbit.com/v1/withdraws/coin"
            data = {"currency": currency,
                    "amount": amount,
                    "address": address,
                    "transaction_type": transaction_type}
            if secondary_address:
                data["secondary_address"] = secondary_address
            headers = await self._request_headers(data)
            body, remain = await _send_post_request(url, headers=headers, data=data)
            return (body, remain) if contain_req else body
        except Exception as e:
            raise e

    async def generate_coin_address(self, ticker, contain_req: bool = False) -> tuple or dict:
        try:
            url = "https://api.upbit.com/v1/deposits/generate_coin_address"
            data = {"currency": ticker
                    }
            headers = await self._request_headers(data)
            body, remain = await _send_post_request(url, headers=headers, data=data)
            return (body, remain) if contain_req else body
        except Exception as e:
            raise e

    async def get_withdraw_orders(self, contain_req: bool = False) -> tuple or list:
        try:
            url = "https://api.upbit.com/v1/withdraws"
            headers = await self._request_headers()
            body, remain = await _send_get_request(url, headers=headers)
            return (body, remain) if contain_req else body
        except Exception as e:
            raise e

    async def get_order(self,
                        ticker=None,
                        uuids=None,
                        states=None,
                        contain_req: bool = False) -> tuple or list:

        if states is None:
            states = ['wait']

        url = "https://api.upbit.com/v1/orders"
        data = {'states': states,
                'order_by': 'desc'}
        if ticker:
            data['market'] = ticker
        if uuids:
            data['uuids'] = uuids
        headers = await self._request_headers(data)
        body, remain = await _send_get_request(url, headers=headers, data=data)
        return (body, remain) if contain_req else body
