import threading
import time
import json
from kubernetes import client, config, watch
from flask import Flask, jsonify

app = Flask(__name__)
config.load_incluster_config()
custom_api = client.CustomObjectsApi()

CRD_GROUP = "scheduling.mygroup.io"
CRD_VERSION = "v1"
CRD_PLURAL = "appgroups"

# Global cache of appgroup graph
graph_lock = threading.Lock()
appgroup_graph = {}

def fetch_all_appgroups():
    try:
        resp = custom_api.list_cluster_custom_object(CRD_GROUP, CRD_VERSION, CRD_PLURAL)
        for ag in resp.get("items", []):
            process_appgroup(ag)
    except Exception as e:
        print(f"[Controller] Error fetching AppGroups: {e}", flush=True)

def process_appgroup(appgroup):
    name = appgroup["metadata"]["name"]
    spec = appgroup.get("spec", {})
    workloads = spec.get("workloads", [])

    graph = {}
        
    for workload in workloads:
        service_name = workload["name"]
        weight = workload.get("weight", 1.0)  # 默认 weight = 1.0 如果没指定
        graph[service_name] = {
            "weight": weight,
            "dependencies": {}
        }

        for dep in workload.get("dependencies", []):
            dep_name = dep["name"]
            metrics = dep.get("metrics", {})
            graph[service_name]["dependencies"][dep_name] = metrics
            
    with graph_lock:
        appgroup_graph[name] = graph
    print(f"[Controller] Updated graph for AppGroup {name}", flush=True)

def controller_loop():
    print("[Controller] Starting watch loop...", flush=True)
    w = watch.Watch()
    while True:
        try:
            stream = w.stream(custom_api.list_cluster_custom_object, CRD_GROUP, CRD_VERSION, CRD_PLURAL)
            for event in stream:
                print(f"[Controller] Got event: {event['type']} for {event['object']['metadata']['name']}", flush=True)
                obj = event["object"]
                etype = event["type"]
                if etype in ["ADDED", "MODIFIED"]:
                    process_appgroup(obj)
                elif etype == "DELETED":
                    appgroup_graph.pop(obj["metadata"]["name"], None)
        except Exception as e:
            print(f"[Controller] Watch error: {e}", flush=True)
            time.sleep(5)

@app.route("/graph/<appgroup>", methods=["GET"])
def get_appgroup_graph(appgroup):
    with graph_lock:
        if appgroup not in appgroup_graph:
            return jsonify({"error": "AppGroup not found"}), 404
        return jsonify(appgroup_graph[appgroup])

if __name__ == "__main__":
    fetch_all_appgroups()
    threading.Thread(target=controller_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=8090)
