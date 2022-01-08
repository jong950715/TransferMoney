import asyncio




async def routine1():
    while True:
        print('11111111')
        await asyncio.sleep(1)

async def routine2():
    while True:
        print('222222222')
        await asyncio.sleep(2)

async def main():
    loop = None or asyncio.get_event_loop()
    loop.call_soon(asyncio.create_task, routine1())
    loop.call_soon(asyncio.create_task, routine2())
    print("다 부름")
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
    print("끝")