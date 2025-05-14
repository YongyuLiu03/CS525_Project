#!/usr/bin/env python3
import json
import subprocess
from collections import defaultdict

pods_json = subprocess.check_output(["kubectl", "get", "pods", "-A", "-o", "json"])
pods = json.loads(pods_json)

node_counts = defaultdict(int)

for item in pods["items"]:
    spec = item["spec"]
    node = spec.get("nodeName")
    if node:
        node_counts[node] += 1

print("NODE,NUM_PODS")
for node, count in sorted(node_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"{node},{count}")
