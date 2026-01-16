n = int(input())

for i in range(n):
    a, x, y = map(int, input().split())
    if x > y:
        x, y = y, x
    if x <= a <= y:
        print("NO")
    else:
        print("YES")
