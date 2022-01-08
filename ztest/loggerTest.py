import asyncio

from ui.MyLogger import MyLogger, LOGGER_NAME
import logging


async def main():
    await MyLogger.createIns()
    logger = logging.getLogger(LOGGER_NAME)
    logger.error('테스트')


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
