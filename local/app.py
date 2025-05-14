from flask import Flask, request, jsonify
from kubernetes import client, config
import threading, time

app = Flask(__name__)
data_lock = threading.Lock()
node_data = {}  # { nodeName: {"latency": {}, "bandwidth": {}, "lossrate": {}, "timestamp": ...} }

matrix_latency = {}
matrix_bandwidth = {}
matrix_lossrate = {}

def update_matrix(old, new):
    for src, dsts in new.items():
        old.setdefault(src, {})
        for dst, val in dsts.items():
            old[src][dst] = val
            

@app.route("/report", methods=["POST"])
def report():
    content = request.json
    source = content.get("source")
    if not source:
        return "Missing source", 400
    with data_lock:
        node_data[source] = content
    return "OK", 200

@app.route("/topology", methods=["GET"])
def get_topology():
    return jsonify({
        "latency": matrix_latency,
        "bandwidth": matrix_bandwidth,
        "lossrate": matrix_lossrate
    })

def aggregate_and_write():
    config.load_incluster_config()
    api = client.CustomObjectsApi()
    while True:
        time.sleep(60)  # 每分钟聚合并写入 CR
        local_latency = {}
        local_bandwidth = {}
        local_lossrate = {}

        with data_lock:
            for src, info in node_data.items():
                for metric, matrix in [("latency", local_latency), ("bandwidth", local_bandwidth), ("lossrate", local_lossrate)]:
                    if metric not in info:
                        continue
                    matrix.setdefault(src, {})
                    for dst, val in info[metric].items():
                        if dst == "sp25-cs525-1401.cs.illinois.edu":
                            continue
                        matrix[src][dst] = val
        
        update_matrix(matrix_latency, local_latency)
        update_matrix(matrix_bandwidth, local_bandwidth)
        update_matrix(matrix_lossrate, local_lossrate)

        body = {
            "spec": {
                "latency": matrix_latency,
                "bandwidth": matrix_bandwidth,
                "lossrate": matrix_lossrate,
            }
        }

        try:
            api.patch_cluster_custom_object(
                group="scheduling.mygroup.io",
                version="v1",
                plural="networktopologies",
                name="cluster-network",
                body=body,
            )
            print("[Aggregator] NetworkTopology CR updated.", flush=True)
        except Exception as e:
            print("[Aggregator] Failed to update CR:", e, flush=True)

if __name__ == "__main__":
    threading.Thread(target=aggregate_and_write, daemon=True).start()
    app.run(host="0.0.0.0", port=8080)
