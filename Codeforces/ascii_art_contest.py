g, p, c = map(int, input().split())

max_score = max(g, p, c)
min_score = min(g, p, c)

score = max_score - min_score

if score >= 10:
    print("check again")

else:
    x = list((g, p, c))
    y = sorted(x)
    print("final", y[1])
