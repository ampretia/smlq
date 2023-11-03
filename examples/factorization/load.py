import argparse
import requests
import random

queue_name = "input"

parser = argparse.ArgumentParser(description="Load Items into queue")

parser.add_argument(
    "--amount",
    required=False, default=100,
    dest="amount",
    help="how many numbers to create",
    type=int,
)

parser.add_argument(
    "--upper", required=False, default=100, dest="upper", help="upper bound", type=int
)

args = parser.parse_args()

url = f"http://localhost:3000/queue/{queue_name}"
values = [random.randint(1, args.upper) for i in range(args.amount)]
print(values)
for v in values:
    data = {"uid": "", "payload": f"{v}"}

    x = requests.post(url, json=data)
