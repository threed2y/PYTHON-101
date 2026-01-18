n = int(input())
array = list(map(int, input().split()))

array.sort()
count = 0

while len(array) >= 2:
    value = array[0] + array[-1]

    if value % 2 != 0:
        count += 1

    array.pop(0)
    array.pop()

print(count)
