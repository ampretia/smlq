
import json
# import argparse
import requests


from math import gcd

input = f"http://localhost:3000/queue/input"
# output = f"http://localhost:3000/queue/output"

# example busy workload
# https://stackoverflow.com/questions/32871539/integer-factorization-in-python
def factorization(n):
    factors = []

    def get_factor(n):
        x_fixed = 2
        cycle_size = 2
        x = 2
        factor = 1

        while factor == 1:
            for count in range(cycle_size):
                if factor > 1:
                    break
                x = (x * x + 1) % n
                factor = gcd(x - x_fixed, n)

            cycle_size *= 2
            x_fixed = x

        return factor

    while n > 1:
        next = get_factor(n)
        factors.append(next)
        n //= next

    return factors


while True:
    x = requests.get(input)
    if x.status_code == 404:
        break
    v = json.loads(x.text)
    
    factors = factorization(int(v['payload']))
    print(f"{v} --> {factors}")
    
