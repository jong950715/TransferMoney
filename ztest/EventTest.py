import asyncio


async def func1(ev):
    await ev.wait()
    print('func1')


async def func2(ev):
    await ev.wait()
    print('func2')


async def main():
    ev1 = asyncio.Event()

    tasks = [asyncio.create_task(func1(ev1)),
             asyncio.create_task(func2(ev1))
             ]

    await asyncio.wait(tasks, timeout=2)
    ev1.set()
    print('done')


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
