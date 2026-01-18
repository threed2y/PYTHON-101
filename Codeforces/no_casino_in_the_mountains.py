t = int(input())

for i in range(t):
    n, k = map(int, input().split())
    a = list(map(int, input().split()))

    hike = 0
    count = 0
    j = 0

    while j < n:
        if a[j] == 0:
            count += 1

        else:
            count = 0

        if count == k:
            hike += 1
            count = 0
            i += 1

        i += 1

    print(hike)
