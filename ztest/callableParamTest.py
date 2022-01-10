def func1():
    print("1")


def main(f):
    f()
    print(f)
    print(callable(f))


main(func1)
