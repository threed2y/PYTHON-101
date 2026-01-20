a,n = map(int,input().split())
a = list(map(int,input().split()))
count = 0

for i in a:
    for j in a:
        if i == j == 0:
            count += 1
            j +=1

        else:
            count = 0
print(count)

