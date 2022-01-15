import pickle
import time
from decimal import Decimal

TEST_NUM = 1000


def timer(func):
    def wrapper(*args, **kwargs):
        time.sleep(0.5)
        s = time.time()
        res = func(*args, **kwargs)
        t = time.time() - s
        print(func.__name__, t * 1000, 'ms')
        return res

    return wrapper


@timer
def testByPickle(l1):
    l2 = pickle.loads(pickle.dumps(l1))
    l2[3][1] = l2[3][3] * 3
    return l2


@timer
def testByTraversal(l1):
    l2 = [[x for x in line] for line in l1]
    l2[3][1] = l2[3][3] * 3
    return l2


def main():
    l1 = [[Decimal(i * j) for i in range(TEST_NUM)] for j in range(TEST_NUM)]

    testByPickle(l1)
    testByTraversal(l1)
    testByPickle(l1)
    l2 = testByTraversal(l1)

    for x, y in zip(l1, l2):
        for _x, _y in zip(x, y):
            if _x != _y:
                print('wrong', _x, _y)

    '''
    expect
    testByPickle 1643.1212425231934 ms
    testByTraversal 45.494794845581055 ms
    testByPickle 1653.5460948944092 ms
    testByTraversal 45.88007926940918 ms
    wrong 3 27
    '''


if __name__ == '__main__':
    main()
