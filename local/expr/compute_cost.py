# kubectl get pods -n default -o json > pods.json
# kubectl get appgroup boutique > graph.json
# curl http://10.104.60.124:8080/topology > topology.json 
# python network_score_calc.py --pods pods.json --appgroup graph.json --topology topology.json

import json
import math
from collections import defaultdict
from pprint import pprint

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def compute_score(src_node, dst_node, metrics, topo, bounds):
    min_l, max_l, min_b, max_b, min_r, max_r = bounds
    score = 0
    missing = True
    if src_node == dst_node:
        return 80

    if 'latency' in metrics and dst_node in topo['latency'].get(src_node, {}):
        lat = topo['latency'][src_node][dst_node]
        norm_lat = (max_l - lat) / (max_l - min_l)
        score += metrics['latency'] * norm_lat
        missing = False

    if 'bandwidth' in metrics and dst_node in topo['bandwidth'].get(src_node, {}):
        bw = topo['bandwidth'][src_node][dst_node]
        norm_bw = (math.log(bw) - math.log(min_b)) / (math.log(max_b) - math.log(min_b))
        score += metrics['bandwidth'] * norm_bw
        missing = False

    if 'lossrate' in metrics and dst_node in topo['lossrate'].get(src_node, {}):
        lr = topo['lossrate'][src_node][dst_node]
        norm_lr = (max_r - lr) / (max_r - min_r)
        score += metrics['lossrate'] * norm_lr
        missing = False

    if missing:
        return 0

    return score *100

def evaluate_score(placement, graph, topo):
    bounds = topo["minLatency"], topo["maxLatency"], topo["minBandwidth"], topo["maxBandwidth"], topo["minLossrate"], topo["maxLossrate"]
    score_sum = 0.0
    total_weight = 0.0
    per_app_score = defaultdict(float)
    per_app_score_no_rev = defaultdict(float)

    for app, info in graph.items():
        app_nodes = placement.get(app, [])
        if not app_nodes:
            continue

        for dep_app, metrics in info['dependencies'].items():
            dep_nodes = placement.get(dep_app, [])
            if not dep_nodes:
                continue

            forward_sum = 0.0
            for src_node in app_nodes:
                inter_score = sum(compute_score(src_node, dst_node, metrics, topo, bounds) for dst_node in dep_nodes)
                avg_score = inter_score / len(dep_nodes)
                forward_sum += avg_score

            forward_score = (forward_sum / len(app_nodes)) * info['weight']
            score_sum += forward_score
            total_weight += info['weight']
            per_app_score[app] += forward_score
            per_app_score_no_rev[app] += forward_score

            reverse_sum = 0.0
            for dst_node in app_nodes:
                inter_score = sum(compute_score(src_node, dst_node, metrics, topo, bounds) for src_node in dep_nodes)
                avg_score = inter_score / len(dep_nodes)
                reverse_sum += avg_score

            reverse_score = (reverse_sum / len(app_nodes)) * graph[dep_app]['weight']
            score_sum += reverse_score
            total_weight += graph[dep_app]['weight']
            per_app_score[dep_app] += reverse_score

    avg_score = score_sum / total_weight if total_weight > 0 else 0
    return score_sum, avg_score, per_app_score, per_app_score_no_rev

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--pods', required=True, help='path to pods.json')
    parser.add_argument('--topology', required=True, help='path to network_topology.json')
    parser.add_argument('--appgroup', required=True, help='path to appgroup_graph.json')
    args = parser.parse_args()

    pods = load_json(args.pods)
    topology = load_json(args.topology)
    graph_raw = load_json(args.appgroup)

    # parse placement
    placement = defaultdict(list)
    for pod in pods['items']:
        labels = pod['metadata'].get('labels', {})
        app = labels.get('app')
        node = pod['spec'].get('nodeName')
        if app and node:
            placement[app].append(node)

    # parse appgroup
    graph = {}
    for w in graph_raw['spec']['workloads']:
        graph[w['name']] = {
            'weight': w.get('weight', 1.0),
            'dependencies': {d['name']: d['metrics'] for d in w.get('dependencies', [])}
        }

    total, avg, per_app, per_app_no_rev = evaluate_score(placement, graph, topology)
    print(f"Total Score: {total:.3f}")
    print(f"Average Score per App: {avg:.3f}\n")
    print("Per-app Score (with reverse):")
    for app, score in sorted(per_app.items(), key=lambda x: -x[1]):
        print(f"{app:20s}: {score:.3f}")

    print("\nPer-app Score (only forward):")
    for app, score in sorted(per_app_no_rev.items(), key=lambda x: -x[1]):
        print(f"{app:20s}: {score:.3f}")
