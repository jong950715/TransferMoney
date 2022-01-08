import random
import time

TEST_NUM = 10000000

def timer(func):
    def wrapper(*args, **kwargs):
        time.sleep(0.5)
        s = time.time()
        res = func(*args, **kwargs)
        t = time.time() - s
        print(func.__name__, t*1000, 'ms')
        return res

    return wrapper

@timer
def test1(l1, l2):
    l3 = []
    for i, n in enumerate(l1):
        l3.append(n*l2[i])
@timer
def test2(l1, l2):
    l3 = []
    for n1, n2 in zip(l1, l2):
        l3.append(n1*n2)

@timer
def test3(l1, l2):
    l3 = []
    for i in range(len(l1)):
        l3.append(l1[i]*l2[i])

def dummy(r1, r2, r3):
    pass

def main():
    list1 = [random.random() for _ in range(TEST_NUM)]
    list2 = [random.random() for _ in range(TEST_NUM)]


    r1 = test1(list1, list2)
    r2 = test2(list1, list2)
    r3 = test3(list1, list2)

    dummy(r1, r2, r3)



main()