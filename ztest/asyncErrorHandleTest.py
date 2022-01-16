import asyncio


async def errorTask(e):
    if e:
        await asyncio.sleep(3)
        raise Exception(e)
    else:
        return


async def main():
    tasks = [asyncio.create_task(errorTask(True)),
             asyncio.create_task(errorTask(True)),
             asyncio.create_task(errorTask(False))]

    returns, pending = await asyncio.wait(tasks)

    for ret in returns:
        try:
            await ret
            ret.result()
            break
        except Exception as e:
            print(e)

    await asyncio.sleep(3)
    await main()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())