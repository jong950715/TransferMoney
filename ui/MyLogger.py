import asyncio
import logging

from common.SingleTonAsyncInit import SingleTonAsyncInit
from common.createTask import createTask
from definitions import getRootDir

"""
콘솔로그
파일로그
"""
LOGGER_NAME = 'myLogger'
LOGGER_LEVEL = logging.INFO
LOG_FILE_NAME = '/ui/src/transferMoney.log'
EAGER_THREASHOLD = 35
FLUSH_PERIOD = 10


class MyFileHandler(logging.Handler):
    def __init__(self, filename, mode='a', encoding="UTF-8", errors=None):
        logging.Handler.__init__(self)
        self.file = open(filename, mode, encoding=encoding, errors=errors)
        self.run()

    def close(self):
        self.file.close()
        logging.Handler.close(self)

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        self.file.write(msg)
        if record.levelno > EAGER_THREASHOLD:
            self.myFlush()

    def myFlush(self) -> None:
        # Sync flush is fast enough
        self.file.flush()

    async def _run(self):
        while True:
            await asyncio.sleep(FLUSH_PERIOD)
            self.myFlush()

    def run(self):
        asyncio.get_event_loop().call_soon(createTask, self._run())


class MyLogger(SingleTonAsyncInit):
    logger = None

    async def _asyncInit(self):
        self.logger = logging.getLogger(LOGGER_NAME)
        self.__class__.logger = self.logger
        self.logger.setLevel(LOGGER_LEVEL)
        formatter = logging.Formatter(
            '|%(asctime)s|'
            '\t##%(levelname)s##'
            '\t%(message)s'
            '\t >> File "%(filename)s", line %(lineno)s, in %(module)s\n')

        self.consoleHandler = logging.StreamHandler()
        self.fileHandler = MyFileHandler(filename=getRootDir() + LOG_FILE_NAME)

        self.handlers = [self.consoleHandler, self.fileHandler]

        for h in self.handlers:
            h.setFormatter(formatter)
            self.logger.addHandler(h)

    @classmethod
    def getLogger(cls):
        if cls.logger:
            return cls.logger
        else:
            raise Exception("생성이 안됨 초기화 후 사용 바람")

    async def run(self):
        # flush every 10seconds
        while True:
            await asyncio.sleep(5)


async def example():
    myLogger = await MyLogger.getIns()

    MyLogger.getInsSync().setPeriodOfFlagName('flagB', 30)
    MyLogger.getInsSync().setPeriodOfFlagName('flagC', 10)

    tasks = []
    tasks.append(asyncio.create_task(myLogger.run()))
    tasks.append(asyncio.create_task(test1()))
    await asyncio.wait(tasks)


async def test1():
    if MyLogger.getInsSync().checkFlags('flagA') is False:
        MyLogger.getInsSync().getLogger().warning('flagA_60sec')

    if MyLogger.getInsSync().checkFlags('flagB') is False:
        MyLogger.getInsSync().getLogger().warning('flagB_30sec')

    if MyLogger.getInsSync().checkFlags('flagC') is False:
        MyLogger.getInsSync().getLogger().warning('flagC_10sec')

    await asyncio.sleep(0.01)


if __name__ == '__main__':
    loop_ = asyncio.get_event_loop()
    loop_.run_until_complete(example())
