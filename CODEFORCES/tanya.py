
t = int(input().strip())
for i in range(t):
    n = int(input().strip())
    a = input().split()

    s = ""
    for j in a:
        if j + s < s + j:
            s = j+s
        else:
            s = s+j

    print(s)

