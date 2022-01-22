import sys


def main(arg1=0,arg2=0,arg3=0):
    v = input()
    try:
        v = int(v)
    except ValueError:
        v = float(v)
    print(((v*0.543)+(5.228**(54/23.5543))))


if __name__ == '__main__':
    try:
        print(f"returned: {main(*sys.argv[1:4]) or 0}")
    except NameError:
        print("Entry point 'main' not defined")

