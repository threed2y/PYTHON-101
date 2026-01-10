# 6A CODEFORCES

a = list(map(int, input().split()))
a.sort()

if a[0] + a[1] > a[2] or a[1] + a[2] > a[3]:
    print("TRIANGLE")
elif a[0] + a[1] == a[2] or a[1] + a[2] == a[3]:
    print("SEGMENT")
else:
    print("IMPOSSIBLE")
