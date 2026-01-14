n = int(input())

for i in range(n):
    bracket = input().strip()
    checksum = 0
    ok = 0
    for seq in bracket:
        if seq == ")":
            checksum += 1
        else:
            checksum -= 1

        if checksum == 0:
            ok += 1

    if ok == 1:
        print("NO")
    else:
        print("YES")
