from datetime import datetime

print(datetime.strptime("2018-01-31", "%Y-%m-%d"))

s = '2022-01-13T20:50:28+09:00'
#s = '2022-01-13T21:26:28'

print(datetime.strptime(s, "%Y-%m-%dT%H:%M:%S%z").timestamp())

print(datetime.now().timestamp())

res = {}