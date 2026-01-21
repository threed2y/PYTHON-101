import sys

input = sys.stdin.readline

for i in range(int(input())):
    n, k = map(int, input().split())

    print(k << n)
