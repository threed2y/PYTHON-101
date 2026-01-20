n = int(input())
a = list(map(int, input().split()))
count = 0

for i in range(n):
    for j in range(len(a)):
        if a[i] > a[j] and i <= j:
            a = a.pop(j)
            count += 1

        else:
            print(0)
