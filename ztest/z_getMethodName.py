
import re

from selfLib.UpbitExtra import UpbitExtra

methods = (dir(UpbitExtra))

regex = re.compile('^[a-zA-Z][a-zA-Z_]+[a-zA-Z]$')

res = []
for method in methods:
    if regex.match(method):
        res.append(method)

frame = 'async def {0}(self, *args, **kwargs):\n\tawait super(UpClient, self).{0}(*args, **kwargs)\n'
frame = 'async def {0}(self, *args, **kwargs):\n\treturn await super(UpClient, self).{0}(*args, **kwargs)\n'
for r in res:
    print(frame.format(r))


'''
async def buy_limit_order(self, *args, **kwargs):
    return await super(UpClient, self).buy_limit_order(*args, **kwargs)
'''