
data = input().split()

n = int(data[0])
a = map(int, data[1:])

current_sum = 0

for x in a:
    current_sum += x

    if current_sum % 2 == 0:
        current_sum = 0

print(current_sum)
