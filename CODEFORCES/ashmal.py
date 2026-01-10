n = int(input())
arr = input().split()

s = ""
for x in arr:
    s = min(x + s, s + x)

print(s)
