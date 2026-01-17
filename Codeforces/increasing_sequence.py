n, d = map(int, input().split())
b = list(map(int, input().split()))

count = 0

for i in range(1, n):
    if b[i] <= b[i - 1]:
        need = b[i - 1] + 1
        dif = need - b[i]
        m = (dif + d - 1) // d
        b[i] += m * d
        count += m

print(count)
