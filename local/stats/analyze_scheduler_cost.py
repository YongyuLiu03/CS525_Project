#!/usr/bin/env python3

import subprocess
import json
import requests

AGGREGATOR_TOPOLOGY_URL = "http://10.104.60.124:8080/topology"
APPGROUP_GRAPH_URL = "http://10.108.70.16:8090/graph/"

def get_pod_locations(label_selector):
    cmd = [
        "kubectl", "get", "pods", "-o", "json", "--selector", label_selector
    ]
    pods = json.loads(subprocess.check_output(cmd))
    pod_to_node = {}
    for pod in pods["items"]:
        name = pod["metadata"]["name"]
        node = pod["spec"].get("nodeName", "")
        app = pod["metadata"]["labels"].get("app", "")
        if node:
            pod_to_node[app] = node
    return pod_to_node

def fetch_topology():
    resp = requests.get(AGGREGATOR_TOPOLOGY_URL)
    return resp.json()

def fetch_appgraph(appgroup):
    resp = requests.get(APPGROUP_GRAPH_URL + appgroup)
    return resp.json()

def compute_comm_cost(appgroup, pod_nodes, topology, graph):
    total = 0
    for svc, meta in graph.items():
        node_from = pod_nodes.get(svc)
        if not node_from:
            continue
        for dep, metrics in meta.get("dependencies", {}).items():
            node_to = pod_nodes.get(dep)
            if not node_to or node_to not in topology["latency"].get(node_from, {}):
                continue
            cost = 0
            if "latency" in metrics:
                maxlat = topology["maxLatency"] or 1.0
                cost += metrics["latency"] * (topology["latency"][node_from][node_to] / maxlat)
            if "bandwidth" in metrics:
                maxbw = topology["maxBandwidth"] or 1.0
                bw = topology["bandwidth"][node_from][node_to]
                if bw > 0:
                    cost += metrics["bandwidth"] * (1.0 / bw) * maxbw
            if "lossrate" in metrics:
                maxloss = topology["maxLossrate"] or 1.0
                cost += metrics["lossrate"] * (topology["lossrate"][node_from][node_to] / maxloss)
            total += cost
    return total

def main():
    topology = fetch_topology()
    graph = fetch_appgraph("medium-microservice-app")

    # 1. 默认调度器部署的前缀
    print("Analyzing default scheduler placement...")
    default_nodes = get_pod_locations("appgroup=medium-microservice-app")
    default_cost = compute_comm_cost("medium-microservice-app", default_nodes, topology, graph)
    print(f"Default scheduler total communication cost: {default_cost:.3f}")

    # 2. 自定义调度器部署
    print("Analyzing network-aware scheduler placement...")
    net_nodes = get_pod_locations("appgroup=medium-microservice-app")
    net_cost = compute_comm_cost("medium-microservice-app", net_nodes, topology, graph)
    print(f"Network-aware scheduler total communication cost: {net_cost:.3f}")

if __name__ == "__main__":
    main()
