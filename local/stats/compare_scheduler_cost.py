#!/usr/bin/env python3

import subprocess
import json
import requests

AGGREGATOR_TOPOLOGY_URL = "http://10.104.60.124:8080/topology"
APPGROUP_GRAPH_URL = "http://10.108.70.16:8090/graph/"
PENALTY_LOCAL_COST = 0.2
METRIC_MISSING_COST = 5

def get_pod_locations(label_selector):
    cmd = ["kubectl", "get", "pods", "-o", "json", "--selector", label_selector]
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
    return requests.get(AGGREGATOR_TOPOLOGY_URL).json()

def fetch_appgraph(appgroup):
    return requests.get(APPGROUP_GRAPH_URL + appgroup).json()

def compute_cost(src, dst, metrics, topo):
    if src == dst:
        return PENALTY_LOCAL_COST

    cost = 0.0
    found = False

    if "latency" in metrics:
        lat = topo["latency"].get(src, {}).get(dst)
        if lat is not None:
            cost += metrics["latency"] * (lat / topo["maxLatency"])
            found = True
    if "bandwidth" in metrics:
        bw = topo["bandwidth"].get(src, {}).get(dst)
        if bw and bw > 0:
            cost += metrics["bandwidth"] * (1.0 - (bw / topo["maxBandwidth"]))
            found = True
    if "lossrate" in metrics:
        lr = topo["lossrate"].get(src, {}).get(dst)
        if lr is not None:
            cost += metrics["lossrate"] * (lr / topo["maxLossrate"])
            found = True

    if not found:
        cost += METRIC_MISSING_COST

    return cost

def compute_comm_cost(appgroup, pod_nodes, topology, graph):
    total = 0.0
    for svc, meta in graph.items():
        src_node = pod_nodes.get(svc)
        if not src_node:
            continue

        # Dependencies (outgoing)
        weight = meta.get("weight", 1.0)
        for dep, metrics in meta.get("dependencies", {}).items():
            dst_node = pod_nodes.get(dep)
            if dst_node:
                total += weight * compute_cost(src_node, dst_node, metrics, topology)

        # Dependents (incoming)
        for other, other_meta in graph.items():
            if svc not in other_meta.get("dependencies", {}):
                continue
            metrics = other_meta["dependencies"][svc]
            dst_node = pod_nodes.get(other)
            if dst_node:
                total += other_meta.get("weight", 1.0) * compute_cost(dst_node, src_node, metrics, topology)

    return total

def main():
    topology = fetch_topology()
    graph = fetch_appgraph("medium-microservice-app")

    print("Analyzing default scheduler placement...")
    default_nodes = get_pod_locations("appgroup=medium-microservice-app")
    default_cost = compute_comm_cost("medium-microservice-app", default_nodes, topology, graph)
    print(f"Default scheduler total communication cost: {default_cost:.3f}")

    # print("Analyzing network-aware scheduler placement...")
    # net_nodes = get_pod_locations("appgroup=medium-microservice-app")
    # net_cost = compute_comm_cost("medium-microservice-app", net_nodes, topology, graph)
    # print(f"Network-aware scheduler total communication cost: {net_cost:.3f}")

if __name__ == "__main__":
    main()
