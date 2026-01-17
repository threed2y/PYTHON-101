import sys

def solve():
    try:
        line = sys.stdin.readline()
        if not line: return
        n = int(line)
        a = list(map(int, sys.stdin.readline().split()))
    except ValueError:
        return

    current_sum = 0
    k = 0

    for x in a:
        if x == -1:
            k += 1
        else:
            current_sum += x

    ans = current_sum + k

    if ans < 0:
        print(0)
    else:
        print(ans)

line = sys.stdin.readline()
if line:
    t = int(line)
    for _ in range(t):
        solve()
