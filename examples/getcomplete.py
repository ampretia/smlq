import argparse
import requests
import time

parser = argparse.ArgumentParser(description="Load Items into queue")

parser.add_argument(
    "--queue", required=True, dest="queue", help="queuename to push to", type=str
)

args = parser.parse_args()
url = f"http://localhost:3000/queue/{args.queue}"

while True:    
    x = requests.get(url)
    if x.status_code == 404:
        break
    print(x.text)
    time.sleep(1)
