class MyList(list):
    KEYS1 = ['ticker', '_price', 'price', 'volume', 'upAsk', 'spBid', 'ftBid', 'upWithdraw', 'bnDeposit']
    KEYS2 = ['ticker', '_price', 'price', 'volume', 'upBid', 'spAsk', 'ftBid', 'bnWithdraw', 'upDeposit']
    LEN = len(KEYS1)
    TO_INDEX = dict()
    for i, (key1, key2) in enumerate(zip(KEYS1, KEYS2)):
        TO_INDEX[key1] = i
        TO_INDEX[key2] = i

    LUT_STR = sorted(list(set(KEYS1 + KEYS2)))
    LUT_INDEX = [None] * len(LUT_STR)

    for i in range(len(LUT_INDEX)):
        LUT_INDEX[i] = TO_INDEX[LUT_STR[i]]

    def __init__(self):
        super(MyList, self).__init__([None] * self.LEN)

    def __getitem__(self, key):
        return super(MyList, self).__getitem__(self.getIndex(key))

    def __setitem__(self, key, value):
        super(MyList, self).__setitem__(self.getIndex(key), value)

    def deepCopy(self):
        res = self.__class__()
        for i, x in enumerate(self):
            res[i] = x

        return res

    def getIndex(self, key):
        if isinstance(key, int):
            return key
        else:
            # return self.TO_INDEX[key]
            return MyList.LUT_INDEX[self.LUT_STR.index(key)]


def test():
    ml = MyList()

    for i, k in enumerate(
            ['ticker', '_price', 'price', 'volume', 'upAsk', 'spBid', 'ftBid', 'upWithdraw', 'bnDeposit']):
        ml[k] = i
    print(ml)

    for x in ml:
        print(x)


if __name__ == '__main__':
    test()
