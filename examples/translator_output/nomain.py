import sys


def nomain():
    return 0


if __name__ == '__main__':
    try:
        print(f"returned: {main(*sys.argv[1:1]) or 0}")
    except NameError:
        print("Entry point 'main' not defined")

