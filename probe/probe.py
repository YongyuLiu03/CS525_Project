import subprocess
import socket
import json
import time
import requests

# 修改为你的所有节点 hostname
TARGETS = [
    # "sp25-cs525-1401.cs.illinois.edu",
    "sp25-cs525-1402.cs.illinois.edu",
    "sp25-cs525-1403.cs.illinois.edu",
    "sp25-cs525-1404.cs.illinois.edu",
    "sp25-cs525-1405.cs.illinois.edu",
    "sp25-cs525-1406.cs.illinois.edu",

    "sp25-cs525-1407.cs.illinois.edu",
    "sp25-cs525-1408.cs.illinois.edu",
    "sp25-cs525-1409.cs.illinois.edu",
    "sp25-cs525-1410.cs.illinois.edu",
    "sp25-cs525-1411.cs.illinois.edu",

    "sp25-cs525-1412.cs.illinois.edu",
    "sp25-cs525-1413.cs.illinois.edu",
    "sp25-cs525-1414.cs.illinois.edu",
    "sp25-cs525-1415.cs.illinois.edu",
    "sp25-cs525-1416.cs.illinois.edu",

    "sp25-cs525-1417.cs.illinois.edu",
    "sp25-cs525-1418.cs.illinois.edu",
    "sp25-cs525-1419.cs.illinois.edu",
    "sp25-cs525-1420.cs.illinois.edu"
]

# 带宽测量间隔（秒）
BANDWIDTH_INTERVAL = 360  # 每小时测一次

last_bandwidth_check = 0

cached_bandwidth = {}


def get_self_hostname():
    return socket.getfqdn()  # 完整 FQDN 最稳妥


def ping_stats(target):
    try:
        output = subprocess.check_output(f"ping -c 5 -W 1 {target}", shell=True, text=True)
        lines = output.splitlines()
        rtt_line = next((line for line in lines if "rtt" in line or "round-trip" in line), "")
        stats_line = next((line for line in lines if "packets transmitted" in line), "")
        if not rtt_line or not stats_line:
            return None  # 不完整信息，跳过
        rtt_avg = float(rtt_line.split("/")[4]) 
        loss_pct = float(stats_line.split(",")[2].strip().split("%")[0])
        # 非常规极端值直接当作失败处理
        if loss_pct >= 100.0 or rtt_avg >= 1000.0:
            return None
        
        return rtt_avg, loss_pct
    except Exception as e:
        print(f"[ping_stats] Error: {e}", flush=True)
        return None
    

def iperf_bandwidth(target):
    try:
        output = subprocess.check_output(
            f"iperf3 -c {target} -t 2 -J", shell=True, text=True, timeout=5
        )
        result = json.loads(output)
        bps = result["end"]["sum_sent"]["bits_per_second"]
        return round(bps / 1e6, 2)  # Mbps
    except Exception as e:
        print(f"Error in iperf_bandwidth: {e}", flush=True)
        return None
    


def main():
    global last_bandwidth_check
    hostname = get_self_hostname()
    timestamp = int(time.time())
    results = {
        "source": hostname,
        "timestamp": timestamp,
        "latency": {},
        "lossrate": {},
        "bandwidth": {}
    }

    check_bandwidth = (timestamp - last_bandwidth_check) >= BANDWIDTH_INTERVAL
    if check_bandwidth:
        last_bandwidth_check = timestamp

        
    for target in TARGETS:
        if target == hostname:
            continue

        ping_result = ping_stats(target)
        if ping_result:
            rtt, loss = ping_result
            results["latency"][target] = rtt
            results["lossrate"][target] = loss

        if target not in cached_bandwidth or check_bandwidth:
            bw = iperf_bandwidth(target)
            if bw is not None:
                cached_bandwidth[target] = bw 

        if target in cached_bandwidth:
            results["bandwidth"][target] = cached_bandwidth[target]

    AGGREGATOR_URL = "http://10.104.60.124:8080/report"
    try:
        response = requests.post(AGGREGATOR_URL, json=results)
        if response.status_code == 200:
            print("Data sent successfully.", flush=True)
        else:
            print(f"Failed to send data: {response.status_code}", flush=True)
    except requests.RequestException as e:
        print(f"Request failed: {e}", flush=True)    
    


if __name__ == "__main__":
    while True:
        main()
        time.sleep(30)