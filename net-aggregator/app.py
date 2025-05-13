from flask import Flask, request, jsonify
from kubernetes import client, config
import threading, time

app = Flask(__name__)
data_lock = threading.Lock()
node_data = {}  # { nodeName: {"latency": {}, "bandwidth": {}, "lossrate": {}, "timestamp": ...} }

matrix_latency = {}
matrix_bandwidth = {}
matrix_lossrate = {}

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
        "lossrate": matrix_lossrate,
        "maxLatency": max([v for dsts in matrix_latency.values() for v in dsts.values()] + [0.001]),
        "maxBandwidth": max([v for dsts in matrix_bandwidth.values() for v in dsts.values()] + [0.001]),
        "maxLossrate": max([v for dsts in matrix_lossrate.values() for v in dsts.values()] + [0.001]),
        "minLatency": min([v for dsts in matrix_latency.values() for v in dsts.values()] ),
        "minBandwidth": min([v for dsts in matrix_bandwidth.values() for v in dsts.values()] ),
        "minLossrate": min([v for dsts in matrix_lossrate.values() for v in dsts.values()] ),
    })

def aggregate_and_write():
    config.load_incluster_config()
    api = client.CustomObjectsApi()
    while True:
        time.sleep(60)  # 每分钟聚合并写入 CR
        local_latency = {}
        local_bandwidth = {}
        local_lossrate = {}
        
        max_latency = 0.001
        max_bandwidth = 0.001
        max_lossrate = 0.001
        min_latency = 1000000
        min_bandwidth = 1000000
        min_lossrate = 1000000

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
                        
                        if metric == "latency":
                            if val > max_latency:
                                max_latency = val
                            if val < min_latency:
                                min_latency = val
                        elif metric == "bandwidth":
                            if val > 0 and val > max_bandwidth:  
                                max_bandwidth = val
                            if val < min_bandwidth:
                                min_bandwidth = val
                        elif metric == "lossrate":
                            if val > max_lossrate:
                                max_lossrate = val
                            if val < min_lossrate:
                                min_lossrate = val
                                
            global matrix_latency, matrix_bandwidth, matrix_lossrate
            matrix_latency = local_latency
            matrix_bandwidth = local_bandwidth
            matrix_lossrate = local_lossrate

        body = {
            "spec": {
                "latency": matrix_latency,
                "bandwidth": matrix_bandwidth,
                "lossrate": matrix_lossrate,
                "maxLatency": max_latency,
                "maxBandwidth": max_bandwidth,
                "maxLossrate": max_lossrate,
                "minLatency": min_latency,
                "minBandwidth": min_bandwidth,
                "minLossrate": min_lossrate,
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




