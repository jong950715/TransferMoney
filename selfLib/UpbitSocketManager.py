import asyncio
import json
from binance import BinanceSocketManager, AsyncClient


class UpbitSocketManager(BinanceSocketManager):
    def __init__(self):
        dummy_cli = AsyncClient('upbit', 'upbit')
        super(UpbitSocketManager, self).__init__(dummy_cli)

    def _get_socket(self, *args, **kwargs):
        subscribe_data = kwargs['subscribe_data']
        if isinstance(subscribe_data, list):
            subscribe_data = json.dumps(subscribe_data)
        if not isinstance(subscribe_data, str):
            raise Exception('subscribe_data의 형식은 list혹은 list의 json 이어야 합니다.')
        del kwargs['subscribe_data']

        kwargs['path'] = ' '
        kwargs['stream_url'] = 'wss://api.upbit.com/websocket/v1'
        kwargs['prefix'] = ''

        res = super(UpbitSocketManager, self)._get_socket(*args, **kwargs)

        res._after_connect = (lambda: res.ws.send(subscribe_data))

        return res

    def getOrderBook(self, symbols, depth=1):
        subscribe_data = [
            {"ticket": "ztest"},
            {"type": "orderbook",
             "codes": []},
            {"format": "SIMPLE"}
        ]
        for sym in symbols:
            subscribe_data[1]['codes'].append('{0}.{1}'.format(sym, depth))

        return self._get_socket(subscribe_data=subscribe_data)


async def example2():
    usm = UpbitSocketManager()
    async with usm.getOrderBook(['KRW-BTC', 'KRW-TRX']) as ws:
        while True:
            msg = await ws.recv()
            print(json.dumps(msg, sort_keys=False, indent=4))


async def example1():
    # given
    subscribe_data = [
        {"ticket": "ztest"},
        {"type": "ticker",
         "codes": ["KRW-BTC"],
         "isOnlyRealtime": True},
        {"format": "SIMPLE"}
    ]
    subscribe_data = json.dumps(subscribe_data)

    # then
    usm = UpbitSocketManager()
    ss = usm._get_socket(subscribe_data=subscribe_data)
    async with ss as s:
        while True:
            msg = await s.recv()
            print(msg)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(example2())
