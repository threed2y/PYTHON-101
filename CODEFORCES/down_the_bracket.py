n = int(input())
checksum = 0
for i in range(n):
    bracket = list(str(input().split()))
    for seq in bracket:
        if seq == ")":
            bracket_new = bracket.remove(")")
            checksum += 1
        else:
            bracket_new = bracket.remove("(")
            checksum -= 1
            break
    if checksum == 0 and checksum < 0:
        print("yes")
    else:
        print("no")
