import asyncio
from decimal import Decimal
from data.dataCommons import *


async def getStepTest():
    testS = []
    for i in range(len(PRICE_LEVELS)):
        testS.append([PRICE_LEVELS[i], PRICE_STEPS[i]])
        testS.append([PRICE_LEVELS[i] * Decimal('1.1'), PRICE_STEPS[i]])
        if i > 0:
            testS.append([PRICE_LEVELS[i] * Decimal('0.9'), PRICE_STEPS[i - 1]])

    res = []
    for i, eo in testS:
        ro = getUpbitPriceStep(i)
        res.append([i, ro])
        if ro != eo:
            print('warning!!', i, eo, ro)

    res.sort(key=lambda x: x[0])
    for r in res:
        print(r)


async def moveStepTest():
    tests = []
    for i in range(len(PRICE_LEVELS)):
        tests.append([[PRICE_LEVELS[i], 5], PRICE_LEVELS[i] + PRICE_STEPS[i] * 5])
        tests.append([[PRICE_LEVELS[i] + PRICE_STEPS[i] * 3, 5], PRICE_LEVELS[i] + PRICE_STEPS[i] * 8])
        if i > 0:
            tests.append([[PRICE_LEVELS[i] + PRICE_STEPS[i] * 3, -5], PRICE_LEVELS[i] - PRICE_STEPS[i - 1] * 2])

    tests.append([[73500000, -100000], 0])

    res = []
    for test, eo in tests:
        ro = getUpbitNextPrice(*test)
        if ro != eo:
            print('이상이상')
        res.append([test, ro])

    for r in res:
        print(r)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(moveStepTest())
