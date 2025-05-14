import subprocess
import socket
import json
import time
import requests

# 修改为你的所有节点 hostname
TARGETS = [
    # "sp25-cs525-1401.cs.illinois.edu",
    "sp25-cs525-1402.cs.illinois.edu",
    "sp25-cs525-1403.cs.illinois.edu"
]

# 带宽测量间隔（秒）
BANDWIDTH_INTERVAL = 3600  # 每小时测一次

last_bandwidth_check = 0


def get_self_hostname():
    return socket.getfqdn()  # 完整 FQDN 最稳妥


def ping_stats(target):
    try:
        output = subprocess.check_output(f"ping -c 5 -W 1 {target}", shell=True, text=True)
        lines = output.splitlines()
        rtt_line = next((line for line in lines if "rtt" in line or "round-trip" in line), "")
        stats_line = next((line for line in lines if "packets transmitted" in line), "")
        rtt_avg = float(rtt_line.split("/")[4]) if rtt_line else 999.0
        loss_pct = float(stats_line.split(",")[2].strip().split("%")[0]) if stats_line else 100.0
        return rtt_avg, loss_pct
    except:
        return 999.0, 100.0


def iperf_bandwidth(target):
    try:
        output = subprocess.check_output(
            f"iperf3 -c {target} -t 2 -J", shell=True, text=True, timeout=5
        )
        result = json.loads(output)
        bps = result["end"]["sum_sent"]["bits_per_second"]
        return round(bps / 1e6, 2)  # Mbps
    except:
        return 0.0


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

        rtt, loss = ping_stats(target)
        results["latency"][target] = rtt
        results["lossrate"][target] = loss

        if check_bandwidth:
            bw = iperf_bandwidth(target)
            results["bandwidth"][target] = bw

    AGGREGATOR_URL = "http://10.104.60.124:8080/report"
    try:
        response = requests.post(AGGREGATOR_URL, json=results)
        if response.status_code == 200:
            print("Data sent successfully.")
        else:
            print(f"Failed to send data: {response.status_code}")
    except requests.RequestException as e:
        print(f"Request failed: {e}")    
    


if __name__ == "__main__":
    while True:
        main()
        time.sleep(30)