start = input().strip()
end = input().strip()

x1 = ord(start[0]) - ord("a")
y1 = int(start[1]) - 1

x2 = ord(end[0]) - ord("a")
y2 = int(end[1]) - 1

moves = []

while x1 != x2 or y1 != y2:
    step = ""
    if x1 < x2:
        x1 += 1
        step += "R"
    elif x1 > x2:
        x1 -= 1
        step += "L"

    if y1 < y2:
        y1 += 1
        step += "U"
    elif y1 > y2:
        y1 -= 1
        step += "D"

    moves.append(step)

print(len(moves))
for m in moves:
    print(m)
