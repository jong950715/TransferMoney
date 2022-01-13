
d = {
    'a':1
}

print(d)

print(d['a'])
try:
    print(d['b'])
except KeyError as e:
    print(e)