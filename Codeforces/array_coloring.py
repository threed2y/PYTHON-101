t = int(input())
hash_list = list()

for _ in range(t):
    n = int(input())
    a = list(map(int,input().split()))

    for i in a:
        if i % 2 == 0:
            hash_list.append("r")
        else:
            hash_list.append("b")

print(hash_list)
