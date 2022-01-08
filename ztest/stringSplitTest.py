import re

sym = 'TRXUSDT'

regex = '(.+)USDT$'
res = re.compile(regex).findall(sym)

if res:
    print(res[0])
else:
    print('땡')