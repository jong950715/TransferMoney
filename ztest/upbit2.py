import asyncio
import aiopyupbit
from config.MyConfigManager import MyConfigManager

async def submitOrder():
    myConfig = await MyConfigManager.createIns()
    configKeys = myConfig.getConfig('configKeys')

    cli = aiopyupbit.Upbit(access=configKeys['upbit']['api_key'], secret=configKeys['upbit']['secret_key'])
    print(await cli.get_balances())


async def main():
    print(await aiopyupbit.get_tickers('KRW'))
    print(await aiopyupbit.get_current_price("KRW-BTC"))
    print(await aiopyupbit.get_current_price(["KRW-BTC", "KRW-XRP"]))
    print(await aiopyupbit.get_ohlcv("KRW-BTC"))


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(submitOrder())
