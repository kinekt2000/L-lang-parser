import sys


def fib(n):
    if (n<=1):
        return n
    return (fib((n-1))+fib((n-2)))


def main():
    n = input()
    try:
        n = int(n)
    except ValueError:
        n = float(n)
    print(fib(n))
    return 0


if __name__ == '__main__':
    try:
        print(f"returned: {main(*sys.argv[1:1]) or 0}")
    except NameError:
        print("Entry point 'main' not defined")

