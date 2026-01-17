k = int(input().strip())
for i in range(k):
    n = int(input().strip())
    a = input().split()
    s = ""
    for j in a:
        a = sorted(a, key=lambda x: (len(x), x))
        if j + s < s + j:
            s = j + s
        else:
            s = s + j

    print(s)
