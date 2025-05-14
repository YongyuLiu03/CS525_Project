#!/usr/bin/env python3
import json
import subprocess

pods_json = subprocess.check_output(["kubectl", "get", "pods", "-A", "-o", "json"])
pods = json.loads(pods_json)

print("NAMESPACE,POD,APP,NODE,STARTTIME")
for item in pods["items"]:
    meta = item["metadata"]
    spec = item["spec"]
    status = item.get("status", {})
    print(f'{meta["namespace"]},{meta["name"]},{meta["labels"].get("app", "-")},{spec.get("nodeName", "-")},{status.get("startTime", "-")}')
