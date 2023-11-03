import argparse
import requests


parser = argparse.ArgumentParser(description="Load Items into queue")

parser.add_argument(
    "--queue", required=True, dest="queue", help="queuename to push to", type=str
)
parser.add_argument(
    "--datafile",
    required=True,
    dest="datafile",
    help="oneline per task treated as text",
    type=str,
)

args = parser.parse_args()

f = open(args.datafile, "r")
lines = f.readlines()


url = f"http://localhost:3000/queue/{args.queue}"

for line in lines:
    data = {"uid":"", "payload": line}

    x = requests.post(url, json=data)
