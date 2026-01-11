t = int(input().strip())
for _ in range(t):
    n = int(input().strip())
    # Read exactly n strings, each on a separate line
    a = [input().strip() for _ in range(n)]

    # Sort using the correct comparator for lexicographically minimal concatenation
    from functools import cmp_to_key

    def compare(x, y):
        if x + y < y + x:
            return -1
        elif x + y > y + x:
            return 1
        else:
            return 0

    a.sort(key=cmp_to_key(compare))
    print(''.join(a))
