import sys


def main(a=0):
    if (20>30):pass
    else:
        print(0)
    empty()
    return 0


def empty():
    pass


if __name__ == '__main__':
    try:
        print(f"returned: {main(*sys.argv[1:2]) or 0}")
    except NameError:
        print("Entry point 'main' not defined")

