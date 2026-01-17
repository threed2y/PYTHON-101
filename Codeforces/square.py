n = int(input())


for i in range(n):
    a, b, c, d = map(int, input().split())
    if a == c == b == d:
        print("yes")
    else:
        print("no")
