#!/usr/bin/env python3
import json
import subprocess
from datetime import datetime

pods_json = subprocess.check_output(["kubectl", "get", "pods", "-A", "-o", "json"])
pods = json.loads(pods_json)

print("NAMESPACE,POD,SCHEDULING_LATENCY(s)")
for item in pods["items"]:
    meta = item["metadata"]
    status = item.get("status", {})
    conditions = status.get("conditions", [])

    scheduled_time = None
    start_time = status.get("startTime")
    for cond in conditions:
        if cond["type"] == "PodScheduled":
            scheduled_time = cond.get("lastTransitionTime")
            break

    if scheduled_time and start_time:
        fmt = "%Y-%m-%dT%H:%M:%SZ"
        delta = datetime.strptime(start_time, fmt) - datetime.strptime(scheduled_time, fmt)
        latency = delta.total_seconds()
        print(f'{meta["namespace"]},{meta["name"]},{latency:.3f}')
