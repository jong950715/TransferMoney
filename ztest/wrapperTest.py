import asyncio


def require(func):
    async def wrapper(*args, **kwargs):
        self = args[0]
        print('전처리')
        await asyncio.sleep(0.5)
        print(await func(*args, **kwargs))
        await asyncio.sleep(0.5)
        print('후처리{0}'.format(self.msg))

    return wrapper

class AP:
    def __init__(self):
        pass

    async def example(self, msg):
        await asyncio.sleep(0.1)
        return msg + 'mmmmm'


class AA(AP):
    def __init__(self):
        super(AA, self).__init__()
        self.msg = 'AA'

    @require
    async def example(self, *args, **kwargs):
        return await super(AA, self).example(*args, **kwargs)





async def main():
    ins = AA()

    tasks = []
    for i in range(5):
        tasks.append(
            asyncio.create_task(
                ins.example('함수에선 이걸 실행해주세요.{0}'.format(i))))

    await asyncio.wait(tasks)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
'''''''''
전처리
함수
후처리
'''''''''
