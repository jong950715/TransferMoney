import asyncio
from datetime import datetime

from common.SingleTonAsyncInit import SingleTonAsyncInit
from common.createTask import RUNNING_FLAG, createTask
from data.configTable.ConfigTable import ConfigTable
from data.dataCommons import *
from binance import AsyncClient as BnClient
from selfLib.UpClient import UpClient
import selfLib.aiopyupbit
import json
from config.MyConfigManager import MyConfigManager
from collections import defaultdict
from decimal import Decimal
from definitions import getRootDir
import re

from ui.MyLogger import MyLogger

'''
입출금 현황 ::dev done
출금 수수료 ::dev done
티커 종류   :: dev done
출금 단위   :: dev done
주소 검증식 :: dev done
입금 주소 :: dev done
최소 주문 수량 :: dev done
호가 :: done
'''


class ExGeneralInfo(SingleTonAsyncInit, ConfigTable):
    async def _asyncInit(self, upCli: UpClient, bnCli: BnClient):
        ConfigTable.__init__(self)

        self.upCli = upCli
        self.bnCli = bnCli
        self.logger = MyLogger.getLogger()
        self.tickers = []

        self.upWalletInfo = defaultdict(dict)
        self.bnWalletInfo = defaultdict(dict)
        self.walletInfo = {'up': self.upWalletInfo,
                           'bn': self.bnWalletInfo
                           }
        '''
        {
            'BTC':  {
                        'fee' : 1.0 (Decimal)
                        'withdraw' : True
                        'deposit' : False
                        'withdrawMin' : 10
                        'withdrawMax' : 99999999
                        'withdrawDecimal' : 0.000001
                        'address1' : 'GCZLCMUM4Q4H324CTT3753P6656CYR4KPLHYFPGYPGE6JVHONGLNRDI5'
                        'address2' : 'SUTg1620822004173' (or None)
                        
                        ##only bn##
                        'regex' : '^(0x)[0-9A-Fa-f]{40}$'
                        
                    }
        }
        '''
        self.upExInfo = defaultdict(dict)
        self.bnSpExInfo = defaultdict(dict)
        self.bnFtExInfo = defaultdict(dict)
        self.exInfo = {'up': self.upExInfo,
                       'sp': self.bnSpExInfo,
                       'ft': self.bnFtExInfo
                       }
        '''
        {
            'BTCUSDT':  {
            'KRW-BTC':  {
                        'qtyStep': 0.00000001
                        'minValue': 5000
                        
                        ##only bn##
                        'minPrice': 1
                        'maxPrice': 10000
                        'priceStep': 0.0001
                        'minQty': 5
                        'maxQty': 10000
                    }
        }
        '''

    async def updateAllInfo(self):
        await self.updateUpWalletInfo()
        await self.updateBnWalletInfo()
        await self.updateUpbitAddress()
        await self.updateBnAddress()
        await self.updateUpExInfo()
        await self.updateBnExInfo()

    def getTickers(self):
        return self.tickers

    def getWalletInfo(self):
        return self.walletInfo

    def getExInfo(self):
        return self.exInfo

    def verifyAddress(self, ticker, address):
        if re.match(self.bnWalletInfo[ticker]['regex'], address):
            return True
        else:
            return False

    async def updateUpExInfo(self):
        self.logger.info('[시작] 업비트 거래소 정보를 받아오고 있습니다.')
        await self.requireUpdateTickers()
        # self.upCli.get_chance(ticker=tickerToUpbitSymbol(ticker))
        # res = await self.upCli.get_chance(ticker='KRW-BTC')
        for ticker in self.tickers:
            sym = tickerToUpbitSymbol(ticker)
            self.upExInfo[sym]['qtyStep'] = Decimal('0.00000001')
            self.upExInfo[sym]['minValue'] = Decimal('5000')
        self.logger.info('[끝] 업비트 거래소 정보를 받아왔습니다.')

    def _updateBnExInfo(self, msg, exInfo):
        for x in msg['symbols']:
            sym = x['symbol']
            ticker = bnSymbolToTicker(x['symbol'])
            # ticker = x['baseAsset']
            if (not ticker) or (ticker not in self.tickers):
                continue
            for fil in x['filters']:
                if fil['filterType'] == 'PRICE_FILTER':  # 'PRICE_FILTER' 'LOT_SIZE' 'MIN_NOTIONAL'
                    exInfo[sym]['minPrice'] = Decimal(fil['minPrice'])
                    exInfo[sym]['maxPrice'] = Decimal(fil['maxPrice'])
                    exInfo[sym]['priceStep'] = Decimal(fil['tickSize'])
                if fil['filterType'] == 'LOT_SIZE':
                    exInfo[sym]['minQty'] = Decimal(fil['minQty'])
                    exInfo[sym]['maxQty'] = Decimal(fil['maxQty'])
                    exInfo[sym]['qtyStep'] = Decimal(fil['stepSize'])
                if fil['filterType'] == 'MIN_NOTIONAL':
                    if 'notional' in fil.keys():
                        exInfo[sym]['minValue'] = Decimal(fil['notional'])
                    if 'minNotional' in fil.keys():
                        exInfo[sym]['minValue'] = Decimal(fil['minNotional'])

    async def updateBnExInfo(self):
        self.logger.info('[시작] 바이낸스 거래소 정보를 받아오고 있습니다.')
        await self.requireUpdateTickers()
        ftex = await self.bnCli.futures_exchange_info()
        spex = await self.bnCli.get_exchange_info()
        self._updateBnExInfo(ftex, self.bnFtExInfo)
        self._updateBnExInfo(spex, self.bnSpExInfo)
        self.logger.info('[끝] 바이낸스 거래소 정보를 받아왔습니다.')

    async def updateBnAddress(self):
        self.logger.info('[시작] 바이낸스 지갑 주소를 받아오고 있습니다.')
        await self.requireUpdateTickers()

        for ticker in self.tickers:
            if self.walletInfo['bn'][ticker]['deposit'] is False:
                continue
            ad = await self.bnCli.get_deposit_address(coin=ticker, network=self._getNetwork(ticker))
            if self.verifyAddress(ticker, ad['address']) and ad['coin'] == ticker:
                self.bnWalletInfo[ticker]['address1'] = ad['address']
                self.bnWalletInfo[ticker]['address2'] = ad['tag']

        self.logger.info('[끝] 바이낸스 지갑 주소를 받아왔습니다.')

    async def updateUpbitAddress(self):
        self.logger.info('[시작] 업비트 지갑 주소를 받아오고 있습니다.')
        ads = await self.upCli.get_deposit_addresses()
        for ad in ads:
            ticker = ad['currency']
            if ticker not in self.tickers:
                continue
            if self.verifyAddress(ticker, ad['deposit_address']):
                self.upWalletInfo[ticker]['address1'] = ad['deposit_address']
                self.upWalletInfo[ticker]['address2'] = ad['secondary_address']
            else:
                self.logger.error('주소가 이상합니다. {0} : {1}'.format(ticker, ad['deposit_address']))
        self.logger.info('[끝] 업비트 지갑 주소를 받아왔습니다.')

    async def requireUpdateTickers(self):
        if len(self.tickers) == 0:
            await self.updateTickers()

    def _getNetwork(self, ticker):
        self.requireLoadConfigCsv()

        try:
            network = self.configCsv[ticker]['network']
        except KeyError:
            raise Exception('networkTable.csv 업데이트가 필요합니다.')

        return network

    async def updateUpWalletInfo(self):
        self.logger.info('[시작] 업비트 지갑 정보를 받아오고 있습니다.')
        await self._upbitDepWitStatus()
        await self._upbitWithdrawFees()
        self.logger.info('[끝] 업비트 지갑 정보를 받아왔습니다.')

    async def updateBnWalletInfo(self):
        self.logger.info('[시작] 바이낸스 지갑 정보를 받아오고 있습니다.')
        await self.requireUpdateTickers()

        bnAllInfo = await self.bnCli.get_all_coins_info()

        res = ''
        for r in bnAllInfo:
            ticker = r['coin']
            if ticker not in self.tickers:
                continue
            for net in r['networkList']:
                if net['network'] == self._getNetwork(ticker):
                    self.bnWalletInfo[ticker]['fee'] = Decimal(net['withdrawFee'])
                    self.bnWalletInfo[ticker]['deposit'] = net['depositEnable']
                    self.bnWalletInfo[ticker]['withdraw'] = net['withdrawEnable']
                    self.bnWalletInfo[ticker]['withdrawMin'] = Decimal(net['withdrawMin'])
                    self.bnWalletInfo[ticker]['withdrawMax'] = Decimal(net['withdrawMax'])
                    self.bnWalletInfo[ticker]['withdrawDecimal'] = Decimal(net['withdrawIntegerMultiple'])
                    self.bnWalletInfo[ticker]['regex'] = net['addressRegex']
                    break
            else:
                raise Exception('network 정보가 상이합니다.', ticker, net)

        self.logger.info('[끝] 바이낸스 지갑 정보를 받아왔습니다.')

    async def _upbitDepWitStatus(self):
        await self.requireUpdateTickers()

        upStatuses = await self.upCli.get_deposit_withdraw_status()
        for res in upStatuses:
            ticker = res['currency']
            if ticker not in self.tickers:
                continue
            state = res['wallet_state']
            if state == 'working':
                self.upWalletInfo[ticker]['withdraw'] = True
                self.upWalletInfo[ticker]['deposit'] = True
            elif state == 'withdraw_only':
                self.upWalletInfo[ticker]['withdraw'] = True
                self.upWalletInfo[ticker]['deposit'] = False
            elif state == 'unsupported' or state == 'paused':
                self.upWalletInfo[ticker]['withdraw'] = False
                self.upWalletInfo[ticker]['deposit'] = False
            elif state == 'deposit_only':
                self.upWalletInfo[ticker]['withdraw'] = False
                self.upWalletInfo[ticker]['deposit'] = True
            else:
                raise Exception('입출금 정보 이상 {0} {1}'.format(ticker, state))

    async def _upbitWithdrawFees(self):
        await self.requireUpdateTickers()

        tasks = []
        for ticker in self.tickers:
            tasks.append(
                asyncio.create_task(
                    self.upCli.get_withdraw_chance(ticker)))

        res = (await asyncio.wait(tasks))[0]

        for r in res:
            r = r.result()
            ticker = r['currency']['code']
            if ticker not in self.tickers:
                continue
            self.upWalletInfo[ticker]['fee'] = Decimal(r['currency']['withdraw_fee'])
            self.upWalletInfo[ticker]['withdrawMin'] = Decimal(r['withdraw_limit']['minimum'])
            if r['withdraw_limit']['onetime']:
                self.upWalletInfo[ticker]['withdrawMax'] = Decimal(r['withdraw_limit']['onetime'])
            else:
                self.upWalletInfo[ticker]['withdrawMax'] = Decimal('1000000000')
            self.upWalletInfo[ticker]['withdrawDecimal'] = Decimal('10') ** (-1 * Decimal(r['withdraw_limit']['fixed']))

    async def updateTickers(self):
        self.logger.info("[시작] 티커 정보를 업데이트를 시작 합니다.")
        upMarkets = await self.upCli.get_markets()  # upMarkets[0]['market'].split('-')[0]
        bnSpInfo = await self.bnCli.get_exchange_info()  # futere에 있으면 여기 무조건 있음. 생략
        bnFtInfo = await self.bnCli.futures_exchange_info()  # bnFtInfo['symbols'][0]['baseAsset']

        bnFtTickers = []
        bnSpTickers = []
        upTickers = []

        for market in upMarkets:
            spl = market['market'].split('-')
            if spl[0] == 'KRW':
                upTickers.append(spl[1])
        for sym in bnFtInfo['symbols']:
            if sym['quoteAsset'] == 'USDT':
                bnFtTickers.append(sym['baseAsset'])

        for sym in bnSpInfo['symbols']:
            if sym['quoteAsset'] == 'USDT':
                bnSpTickers.append(sym['baseAsset'])

        bnSpTickers.sort()
        upTickers.sort()
        bnFtTickers.sort()

        tickers = []

        i = j = k = 0

        while i < len(upTickers) and j < len(bnFtTickers) and k < len(bnSpTickers):
            if upTickers[i] == bnFtTickers[j] and upTickers[i] == bnSpTickers[k]:
                tickers.append(upTickers[i])
                i += 1
                j += 1
                k += 1
            elif upTickers[i] < bnFtTickers[j]:
                if upTickers[i] < bnSpTickers[k]:
                    i += 1
                else:
                    k += 1
            else:
                if bnFtTickers[j] < bnSpTickers[k]:
                    j += 1
                else:
                    k += 1

        self.requireLoadConfigCsv()
        tickers = self.compareTickersToCsv(tickers)

        self.tickers = tickers

        self.logger.info("[끝] 티커 정보를 업데이트가 완료 되었습니다.")
        return tickers

    async def _run(self):
        while RUNNING_FLAG[0]:
            await asyncio.sleep(5)

    def run(self):
        asyncio.get_event_loop().call_soon(createTask, self._run())


async def example():
    await MyConfigManager.getIns()
    configKeys = MyConfigManager.getInsSync().getConfig('configKeys')
    upCli = UpClient(access=configKeys['upbit']['api_key'], secret=configKeys['upbit']['secret_key'])
    bnCli = await BnClient.create(configKeys['binance']['api_key'], configKeys['binance']['secret_key'])

    exInfo = await ExGeneralInfo.createIns(upCli, bnCli)
    tickers = await exInfo.updateTickers()
    print(tickers)
    return
    # await exInfo.updateAllInfo()
    # exInfo.getUpbitPriceStep(Decimal(1000))
    prev = 30
    while True:
        r = await exInfo.upCli.get_order('KRW-ATOM', contain_req=True)
        now = r[1]['sec']
        print('upbitServer remain : ', now)
        if prev < now:
            print(datetime.now().strftime('%M:%S.%f'))
        prev = now


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(example())
