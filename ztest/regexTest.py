import re

hbar = re.compile('^0[.]0[.]\\d{1,6}$')
hbarAddress = '0.0.37073'

res = hbar.match(hbarAddress)

print(res)



