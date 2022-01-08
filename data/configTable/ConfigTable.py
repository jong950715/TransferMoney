import csv
from collections import defaultdict

from definitions import getRootDir

CONFIG_TABLE_CSV = '{0}/data/configTable/configTable.csv'.format(getRootDir())


class ConfigTable:
    def __init__(self):
        self.configCsv = defaultdict(dict)

    def requireLoadConfigCsv(self):
        if self.configCsv is None or len(self.configCsv) == 0:
            self.loadConfigCsv()

    def loadConfigCsv(self):
        with open(CONFIG_TABLE_CSV, 'r') as csvFile:
            self._loadConfigCsv(csvFile)

    def _loadConfigCsv(self, csvFile):
        configTable = csv.reader(csvFile)

        keys = configTable.__next__()[1:]
        for ticker, *line in configTable:
            for i, k in enumerate(keys):
                self.configCsv[ticker][k] = line[i]

        return self.configCsv

    def _addTickerCsv(self, newTickers):
        if isinstance(newTickers, str):
            newTickers = [newTickers]

        if newTickers:
            print('티커가 추가되었습니다. 확인해주세요.', newTickers)

        with open(CONFIG_TABLE_CSV, 'a', newline='') as csvFile:
            csvWriter = csv.writer(csvFile)
            for ticker in newTickers:
                self.configCsv[ticker]['problem'] = 'YES'
                csvWriter.writerow([ticker, '', 'YES'])

    def _removeTickerCsv(self, oldTickers):
        if isinstance(oldTickers, str):
            oldTickers = [oldTickers]

        if oldTickers:
            print('티커가 제거되었습니다. 확인해주세요.', oldTickers)
        for ticker in oldTickers:
            del self.configCsv[ticker]

        newCsv = []
        with open(CONFIG_TABLE_CSV, 'r') as csvFile:
            csvReader = csv.reader(csvFile)
            for i, line in enumerate(csvReader):
                if line[0] not in oldTickers:
                    newCsv.append(line)

        with open(CONFIG_TABLE_CSV, 'w', newline='') as csvFile:
            csvWriter = csv.writer(csvFile)
            csvWriter.writerows(newCsv)

    def compareTickersToCsv(self, after):
        after = self._compareTickersToCsv(after)
        return self._filterTickers(after)

    def _compareTickersToCsv(self, after):
        before = list(self.configCsv.keys())
        before.sort()
        after = list(after)
        after.sort()

        for b, a in zip(before, after):
            if b != a:
                break
        else:
            return after

        adds = []
        removes = []
        for x in after:
            if x not in before:
                adds.append(x)

        for x in before:
            if x not in after:
                removes.append(x)

        self._addTickerCsv(adds)
        self._removeTickerCsv(removes)

        return after

    def _filterTickers(self, tickers):
        exceptionWords = ['YES', 'O', 'OK']
        for ticker, v in self.configCsv.items():
            if v['exception'] and (v['exception'].upper() in exceptionWords):
                tickers.remove(ticker)

        return tickers

    async def printBnNetwork(self):
        await self.requireUpdateTickers()

        bnAllInfo = await self.bnCli.get_all_coins_info()
        network = csv.reader(open(CONFIG_TABLE_CSV, 'r'))

        res = ''
        for r in bnAllInfo:
            ticker = r['coin']
            if ticker in self.tickers:
                netStr = ''
                for net in r['networkList']:
                    netStr += '\t{0}\t{1}'.format(net['network'], net['name'])
                res += ('{0}\t{1}\n'.format(r['coin'], netStr))

        print(res)
