import matplotlib.pyplot as plt
import numpy as np

# schedulers = ["Default", "Custom", "Custom w=1", "Custom w=5"]
# total_scores = [1600.900, 2201.714, 2240.330, 2285.001]  # 你填上其他两个
# avg_scores = [64.293, 88.422, 89.973, 91.767]

# x = np.arange(len(schedulers))
# width = 0.35

# plt.bar(x - width/2, total_scores, width, label='Total Score')

# plt.ylabel('Score')
# plt.xlabel('Scheduler')
# plt.title('Network Score per Scheduler')
# plt.xticks(x, schedulers)
# plt.legend()
# plt.tight_layout()
# plt.show()

# plt.bar(x + width/2, avg_scores, width, label='Avg Score')
# plt.ylabel('Score')
# plt.xlabel('Scheduler')
# plt.title('Network Score per Scheduler')
# plt.xticks(x, schedulers)
# plt.legend()
# plt.tight_layout()
# plt.show()

# default_scores = """frontend            : 464.412
# checkoutservice     : 383.239
# productcatalogservice: 158.464
# recommendationservice: 157.886
# shippingservice     : 135.784
# cartservice         : 82.933
# paymentservice      : 77.070
# currencyservice     : 51.834
# emailservice        : 38.888
# adservice           : 26.235
# redis-cart          : 24.153"""
# custom1_scores = """frontend            : 635.232
# checkoutservice     : 547.548
# cartservice         : 216.417
# productcatalogservice: 168.846
# recommendationservice: 159.457
# shippingservice     : 129.623
# currencyservice     : 129.035
# paymentservice      : 77.135
# redis-cart          : 69.766
# emailservice        : 67.474
# adservice           : 39.798"""

# custom5_scores = """frontend            : 639.561
# checkoutservice     : 561.183
# cartservice         : 219.437
# productcatalogservice: 166.436
# recommendationservice: 150.560
# shippingservice     : 148.481
# currencyservice     : 142.179
# paymentservice      : 78.679
# redis-cart          : 69.523
# emailservice        : 68.963
# adservice           : 39.999"""

# custom_scores = """frontend            : 616.098
# checkoutservice     : 607.573
# cartservice         : 229.928
# shippingservice     : 159.410
# currencyservice     : 150.688
# productcatalogservice: 134.751
# paymentservice      : 79.621
# emailservice        : 69.813
# redis-cart          : 69.646
# recommendationservice: 44.416
# adservice           : 39.771"""

# services = ['frontend', 'checkoutservice', 'productcatalogservice', 'recommendationservice', 'shippingservice', 'cartservice', 'paymentservice', 'currencyservice', 'emailservice', 'adservice', 'redis-cart']
# default_scores = [float(s.split(":")[1].strip()) for s in default_scores.split("\n")]
# custom_scores = [float(s.split(":")[1].strip()) for s in custom_scores.split("\n")]
# custom1_scores = [float(s.split(":")[1].strip()) for s in custom1_scores.split("\n")]
# custom5_scores = [float(s.split(":")[1].strip()) for s in custom5_scores.split("\n")]


# x = np.arange(len(services))
# width = 0.2
colors = ["#4E79A7", "#F28E2B", "#E15759", "#76B7B2"]  # Zone A-D

# plt.bar(x - 1.5*width, default_scores, width, label='Default', color=colors[0])
# plt.bar(x - 0.5*width, custom_scores, width, label='Custom',  color=colors[1])
# plt.bar(x + 0.5*width, custom1_scores, width, label='Custom w=1',  color=colors[2])
# plt.bar(x + 1.5*width, custom5_scores, width, label='Custom w=5',  color=colors[3])

# plt.ylabel('Score')
# plt.xlabel('Service')
# plt.title('Per-App Score by Scheduler')
# plt.xticks(x, services, rotation=45)
# plt.legend()
# plt.tight_layout()
# plt.show()


import pandas as pd
import matplotlib.pyplot as plt

# 定义每个 CSV 文件路径及其标签
scheduler_files = {
    "Default": "online_boutique/default/locust.csv",
    "Custom": "online_boutique/onlycustom/locust.csv",
    "Custom w=1": "online_boutique/customweight1/locust2.csv",
    "Custom w=5": "online_boutique/customweight5/locust.csv"
}




# 定义函数估算 boxplot 所需统计量
def estimate_boxplot_stats(row, label):
    median = row["50%"]
    q3 = row.get("75%", row.get("66%", median))
    q1 = max(2 * median - q3, row["Min Response Time"])
    return {
        "med": median,
        "q1": q1,
        "q3": q3,
        "whislo": row["Min Response Time"],
        "whishi": row["Max Response Time"],
        "label": label
    }

# 为每个 scheduler 构造 boxplot 数据
stats = []
for label, path in scheduler_files.items():
    df = pd.read_csv(path)
    row = df.iloc[-1]  # 假设只有一行 aggregated 数据
    stats.append(estimate_boxplot_stats(row, label))

# 画图
fig, ax = plt.subplots()
boxes = ax.bxp(stats, showfliers=False, patch_artist=True)  # <- patch_artist=True 允许着色

# 设置颜色
for patch, color in zip(boxes['boxes'], colors):
    patch.set_facecolor(color)

# 美化
ax.set_title("Response Time Distribution")
ax.set_ylabel("Response Time (ms)")
plt.tight_layout()
plt.show()