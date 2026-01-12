n = int(input())
s = ""

for i in range(n):
    s += input()

    s = s.strip()
    a = 0
    for i in s:
        if i == "(":
            a += 1

        else:
            a -= 1

    if a == 0:
        print("yes")
    else:
        print("no")
