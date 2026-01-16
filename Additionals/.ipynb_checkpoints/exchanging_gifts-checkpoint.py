n, m = map(int, input().split())

given = [0] * (n + 1)
recieved = [0] * (n + 1)

for i in range(0, m):
    a, b = map(int, input().split())
    given[a] += 1
    recieved[b] += 1


youngest_member = -1

for k in range(1, n + 1):
    if given[k] == 0 and recieved[k] == n - 1:
        youngest_member = k
        break

print(youngest_member)
