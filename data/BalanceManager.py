# get_balances
import asyncio

from collections import defaultdict
from decimal import Decimal

from common.SingleTonAsyncInit import SingleTonAsyncInit
from config.MyConfigManager import MyConfigManager
from data.dataCommons import tickerToBnSymbol, bnSymbolToTicker, toDecimal
from selfLib.UpClient import UpClient
from binance import AsyncClient as BnClient


class BalanceManager(SingleTonAsyncInit):
    async def _asyncInit(self, upCli: UpClient, bnCli: BnClient):
        self.upCli = upCli
        self.bnCli = bnCli

        # xxBalance['BTC'] = 10000
        self.upBalance = defaultdict(Decimal)
        self.spBalance = defaultdict(Decimal)
        self.ftBalance = defaultdict(Decimal)

        self.balances = {'up': self.upBalance,
                         'sp': self.spBalance,
                         'ft': self.ftBalance
                         }

    def getBalances(self):
        return self.balances

    async def updateBalances(self, tickers):
        tasks = [asyncio.create_task(self.updateUpBalance()),
                 asyncio.create_task(self.updateSpBalance(tickers)),
                 asyncio.create_task(self.updateFtBalance(tickers))]

        await asyncio.wait(tasks)

    async def updateUpBalance(self):
        res = await self.upCli.get_balances()
        for r in res:
            self.upBalance[r['currency']] = r['balance']

    async def updateSpBalance(self, tickers):
        tickers = set(tickers)
        tickers.add('USDT')

        res = await self.bnCli.get_account()
        for r in res['balances']:
            ticker = r['asset']
            if ticker in tickers:
                self.spBalance[ticker] = Decimal(r['free']) + Decimal(r['locked'])

    async def updateFtBalance(self, tickers):
        res = await self.bnCli.futures_account_balance()
        usd = Decimal('0')
        for r in res:
            if r['asset'] == 'USDT' or r['asset'] == 'BUSD':
                usd += toDecimal(r['balance'])

        self.ftBalance['USDT'] = usd

        if not tickers:
            return

        tasks = [asyncio.create_task(self.bnCli.futures_position_information(symbol=tickerToBnSymbol(ticker))) for ticker in tickers]
        returns, pending = await asyncio.wait(tasks)

        for ret in returns:
            msg = ret.result()[0]

            tic = bnSymbolToTicker(msg['symbol'])
            amt = msg['positionAmt']
            self.ftBalance[tic] = Decimal(amt)


async def example():
    await MyConfigManager.getIns()
    configKeys = MyConfigManager.getInsSync().getConfig('configKeys')
    upCli = UpClient(access=configKeys['upbit']['api_key'], secret=configKeys['upbit']['secret_key'])
    bnCli = await BnClient.create(configKeys['binance']['api_key'], configKeys['binance']['secret_key'])

    balanceManager = await BalanceManager.createIns(upCli, bnCli)
    res = await balanceManager.updateBalances([])
    print(res)



if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(example())
