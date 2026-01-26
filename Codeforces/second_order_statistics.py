n = int(input())
m = set(map(int, input().split()))

sorted_m = sorted(m)

for i in sorted_m:
    if i > min(m):
        print(i)
        break

    elif len(m) == 1:
        print("NO")
