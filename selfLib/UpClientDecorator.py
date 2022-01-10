import asyncio

def checkRemainGeneral(func):
    async def wrapper(*args, **kwargs):
        self = args[0]
        while self.generalRemains < 2:
            await asyncio.sleep(0.1)
        self.generalRemains -= 1

        return await func(*args, **kwargs)

    return wrapper


def checkRemainOrder(func):
    async def wrapper(*args, **kwargs):
        self = args[0]
        while self.orderRemains < 2:
            await asyncio.sleep(0.1)
        self.orderRemains -= 1

        return await func(*args, **kwargs)

    return wrapper