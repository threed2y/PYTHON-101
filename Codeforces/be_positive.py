t = int(input())

for _ in range(t):
    n = int(input())
    a = list(map(int, input().split()))

    zeros = a.count(0)
    neg = a.count(-1)

    operations = zeros

    if neg % 2 == 1:
        operations += 2

    print(operations)
