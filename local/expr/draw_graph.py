
import json
import math
from collections import defaultdict
from pprint import pprint

import pandas as pd
import matplotlib.pyplot as plt
import argparse

import numpy as np



def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)
    
    
    
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--dpods', required=True, help='path to pods.json')
    parser.add_argument('--cpods', required=True, help='path to pods.json')
    parser.add_argument('--c1pods', required=True, help='path to pods.json')
    parser.add_argument('--c5pods', required=True, help='path to pods.json')
    
    args = parser.parse_args()

    dpods = load_json(args.dpods)
    cpods = load_json(args.cpods)
    c1pods = load_json(args.c1pods)
    c5pods = load_json(args.c5pods)
    
    zones = {
        'Zone A': range(1402, 1407),
        'Zone B': range(1407, 1412),
        'Zone C': range(1412, 1417),
        'Zone Far': range(1417, 1421)
    }

    schedulers = {"Default":dpods, "Custom":cpods, "Custom w=1":c1pods, "Custom w=5":c5pods}
    
    placements = {}
    # parse placement
    
    for s, pods in schedulers.items():
    
        placement = defaultdict(list)
        for pod in pods['items']:
            labels = pod['metadata'].get('labels', {})
            app = labels.get('app')
            node = pod['spec'].get('nodeName')
            shortname = int(node.split("-")[2].split(".")[0])
            if app and node:
                placement[app].append(shortname)
        
        placements[s] = placement
    
    
    pprint(placements)
    exit()
    
    results = {sched: defaultdict(int) for sched in placements}
    
    for sched, mapping in placements.items():
        for _, nodes in mapping.items():
            for n in nodes:
                for zone, zone_nodes in zones.items():
                    if n in zone_nodes:
                        results[sched][zone] += 1
    # python3 draw_graph.py --dpods online_boutique/default/pods.json --cpods online_boutique/onlycustom/pods2.json --c1pods online_boutique/customweight1/pods2.json --c5pods online_boutique/customweight5/pods.json
    
    pprint(results)
    


    x = ["Default", "Custom", "Custom w=1", "Custom w=5"]
    y_zone_a = np.array([1, 10, 6, 6])
    y_zone_b = np.array([4, 0, 0, 5])
    y_zone_c = np.array([4, 0, 5, 0])
    y_zone_far = np.array([2, 1, 0, 0])

    # 累计底部高度
    bottom1 = y_zone_a
    bottom2 = bottom1 + y_zone_b
    bottom3 = bottom2 + y_zone_c

    # 使用更美观的颜色
    colors = ["#4E79A7", "#F28E2B", "#E15759", "#76B7B2"]  # Zone A-D

    plt.bar(x, y_zone_a, color=colors[0], label='Zone A')
    plt.bar(x, y_zone_b, bottom=bottom1, color=colors[1], label='Zone B')
    plt.bar(x, y_zone_c, bottom=bottom2, color=colors[2], label='Zone C')
    plt.bar(x, y_zone_far, bottom=bottom3, color=colors[3], label='Zone FAR')
    plt.xlabel("Scheduler")
    plt.ylabel("Number of Pods")
    plt.title("Pod Placement Distribution Across Zones")
    plt.legend()
    plt.tight_layout()
    plt.show()

