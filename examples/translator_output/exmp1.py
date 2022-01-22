import sys


def main():
    a = -10
    b = 30
    c = ((b-a)**2)
    print((not ((b-6)>25) or ((2**8)==c)))
    d = input()
    try:
        d = int(d)
    except ValueError:
        d = float(d)
    return (((b*a)/c)+d)


if __name__ == '__main__':
    try:
        print(f"returned: {main(*sys.argv[1:1]) or 0}")
    except NameError:
        print("Entry point 'main' not defined")

