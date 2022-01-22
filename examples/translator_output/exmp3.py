import sys


def foo(a,b,c):
    print(a)
    print(b)
    print(c)
    return ((a+b)+c)


def bar(a,b,c):
    return ((a*b)/c)


def main():
    a = 10.7
    b = 0.92
    c = input()
    try:
        c = int(c)
    except ValueError:
        c = float(c)
    print((foo(a, b, c)-bar(a, b, c)))


if __name__ == '__main__':
    try:
        print(f"returned: {main(*sys.argv[1:1]) or 0}")
    except NameError:
        print("Entry point 'main' not defined")

