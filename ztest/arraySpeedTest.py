import random
import time
from array import array
import numpy as np

TEST_NUM = 1000000

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
def test1():
    arr1 = array('d', [0]*TEST_NUM)
    arr2 = array('d', [0]*TEST_NUM)
    arr3 = array('d', [0]*TEST_NUM)

    for i in range(TEST_NUM):
        arr1[i] = random.random()
        arr2[i] = random.random()

    for i in range(TEST_NUM-1):
        arr3[i] = arr1[i]*arr2[i]
@timer
def test2():

    arr1 = np.zeros(TEST_NUM)
    arr2 = np.zeros(TEST_NUM)
    arr3 = np.zeros(TEST_NUM)

    for i in range(TEST_NUM):
        arr1[i] = random.random()
        arr2[i] = random.random()

    for i in range(TEST_NUM - 1):
        arr3[i] = arr1[i] * arr2[i]

@timer
def test3():
    l1 = [0 for _ in range(TEST_NUM)]
    l2 = [0 for _ in range(TEST_NUM)]
    l3 = [0 for _ in range(TEST_NUM)]

    for i in range(TEST_NUM):
        l1[i] = random.random()
        l2[i] = random.random()

    for i in range(TEST_NUM - 1):
        l3[i] = l1[i] * l2[i]

def dummy(r1, r2, r3):
    pass

def main():
    # list1 = [random.random() for _ in range(TEST_NUM)]
    # list2 = [random.random() for _ in range(TEST_NUM)]


    r1 = test1()
    r2 = test2()
    r3 = test3()

    dummy(r1, r2, r3)



main()