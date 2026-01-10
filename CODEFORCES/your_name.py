from collections import Counter

a = int(input())

for i in range(a):
    n = int(input())  # ADDITION OF THIS ONE
    p, q = input().split()

    if Counter(p) == Counter(q):
        print("YES")
    else:
        print("NO")

# SECOND WAY -- REJECTED --- RUNTIME ERROR
# b = int(input())
# for i in range(b):
#    g,h = input().split()

#   if sorted(g) == sorted(h):
#       print("YES")
#   else:
#        print("NO")
