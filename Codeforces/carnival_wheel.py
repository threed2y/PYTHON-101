from math import gcd

n = int(input())

for i in range(n):
    l, a, b = map(int, input().split())
    great = gcd(l, b)

    ans = a + ((l - 1 - a) // great) * great

    print(ans)
