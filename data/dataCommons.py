import asyncio
import re
from decimal import Decimal

from config.MyConfigManager import MyConfigManager

from binance import AsyncClient as BnClient
from selfLib.UpClient import UpClient

'''
ticker : BTC
Symbol :
'''

D2_000_000 = Decimal('2000000')
D1_000_000 = Decimal('1000000')
D500_000 = Decimal('500000')
D100_000 = Decimal('100000')
D10_000 = Decimal('10000')
D1_000 = Decimal('1000')
D500 = Decimal('500')
D100 = Decimal('100')
D50 = Decimal('50')
D10 = Decimal('10')
D5 = Decimal('5')
D1 = Decimal('1')
D0 = Decimal('0')
D0_1 = Decimal('0.1')
D0_01 = Decimal('0.01')
D0_001 = Decimal('0.001')
D0_0001 = Decimal('0.0001')

PRICE_STEPS = (D0_0001, D0_001, D0_01, D0_1, D1, D5, D10, D50, D100, D500, D1_000)
PRICE_LEVELS = (D0, D0_1, D1, D10, D100, D1_000, D10_000, D100_000, D500_000, D1_000_000, D2_000_000)

'''
2,000,000       		1,000
1,000,000	2,000,000	500
500,000	1,000,000	100
100,000	500,000	50
10,000	100,000	10
1,000	10,000	5
100	1,000	1
10	100	0.1
1	10	0.01
0.1	1	0.001
0	0.1	0.0001
'''


def _getUpbitPriceStep(price):
    l = 0
    r = 10
    m = (l + r) // 2

    while r - l != 0:
        if price < PRICE_LEVELS[m]:
            r = m - 1
        else:
            l = m
        m = (l + r + 1) // 2

    return PRICE_STEPS[m], m


def getUpbitPriceStep(price):
    return _getUpbitPriceStep(price)[0]


def getUpbitNextPrice(price, step):
    if not isinstance(step, int):
        step = int(step)
    step = Decimal(step)

    priceStep, m = _getUpbitPriceStep(price)
    newPrice = price + priceStep * step

    if m == 10 and PRICE_LEVELS[m] <= newPrice:
        return newPrice
    if PRICE_LEVELS[m] <= newPrice < PRICE_LEVELS[m + 1]:
        return newPrice

    if step > 0:
        newStep = step - (PRICE_LEVELS[m + 1] - price) // priceStep
        return getUpbitNextPrice(PRICE_LEVELS[m + 1], newStep)
    else:
        newStep = step - (PRICE_LEVELS[m] - price) // priceStep
        return getUpbitNextPrice(PRICE_LEVELS[m] - PRICE_STEPS[m - 1], newStep + 1)


def symbolToTicker(ex, symbol):
    if ex == 'up':
        return upbitSymbolToTicker(symbol)
    elif ex == 'sp' or ex == 'ft' or ex == 'bn':
        return bnSymbolToTicker(symbol)
    else:
        raise Exception('등록되지 않은 거래소 닉네임 입니다. :', ex)


def tickerToSymbol(ex, ticker):
    if ex == 'up':
        return tickerToUpbitSymbol(ticker)
    elif ex == 'sp' or ex == 'ft' or ex == 'bn':
        return tickerToBnSymbol(ticker)
    else:
        raise Exception('등록되지 않은 거래소 닉네임 입니다. :', ex)


def upbitSymbolToTicker(symbol):
    return symbol.split('-')[1]


def tickerToUpbitSymbol(ticker):
    return 'KRW-{0}'.format(ticker)


BN_SYM_TO_TIC_RE = re.compile('(.+)USDT$')
BN_SYM_TO_TIC_LU = dict()


def bnSymbolToTicker(symbol):
    if symbol in BN_SYM_TO_TIC_LU.keys():
        return BN_SYM_TO_TIC_LU[symbol]

    res = BN_SYM_TO_TIC_RE.findall(symbol)
    if res:
        BN_SYM_TO_TIC_LU[symbol] = res[0]
        return BN_SYM_TO_TIC_LU[symbol]
    else:
        return False  # like BTC market


def tickerToBnSymbol(ticker):
    return '{0}USDT'.format(ticker)


def toDecimal(num):
    if isinstance(num, float):
        return Decimal(str(num))
    if isinstance(num, str) or isinstance(num, int):
        return Decimal(num)
    if isinstance(num, Decimal):
        return num


async def example1():
    # bnSymbolToTicker 검증
    await MyConfigManager.getIns()
    configKeys = MyConfigManager.getInsSync().getConfig('configKeys')
    upCli = UpClient(access=configKeys['upbit']['api_key'], secret=configKeys['upbit']['secret_key'])
    bnCli = await BnClient.create(configKeys['binance']['api_key'], configKeys['binance']['secret_key'])

    from data.ExGeneralInfo import ExGeneralInfo
    exInfo = await ExGeneralInfo.createIns(upCli, bnCli)
    tickers = list(await exInfo.updateTickers())
    bnSymbols = list(map(lambda x: '{0}USDT'.format(x), tickers))
    newTickers = list(map(bnSymbolToTicker, bnSymbols))

    newTickers.sort()
    tickers.sort()

    for i in range(len(newTickers)):
        if tickers[i] != newTickers[i]:
            raise Exception('다름')
    else:
        print('같음')


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(example1())
