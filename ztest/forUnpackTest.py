l = [[i*j for i in range(1, 4)]for j in range(1, 4)]

print(l)

for x, *y in l:
    print(x, y)


l1 = ['1', '2', '3']
l2 = ['a', 'b', 'c']

for x in zip(l1, l2):
    print(x)