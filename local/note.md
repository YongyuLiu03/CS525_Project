# install k8s

(https://infotechys.com/install-a-kubernetes-cluster-on-rhel-9/)

先一个master node，两个worker node，nginx测试

version v1.32

# network aware 配置

## 流程

[每台 Node 上]
  network-probe-agent Pod
     ↓  采集 RTT、带宽（用 ping / iperf3）python
     ↓
[中心组件]
  汇总所有节点间网络数据
     ↓
  用 K8s client-go 创建 / 更新 NetworkTopology CR python
     ↓
[调度时]
  NetworkScorePlugin 调用 client-go 读取该 CR go
     ↓
  在 Score() 中打分

## 收集数据，each pod

DeamonSet for probing
(https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/)

gather network metric: ping, iperf

network-probe-agent 需要安装了ping和iperf3的镜像，probe.py用configmap传入，作为network-probe-script

## crd

定义crd

需要crd.yaml and sample.yaml，然后apply
(https://kubernetes.io/docs/tasks/extend-kubernetes/custom-resources/custom-resource-definitions/)

写中心汇总器， python flask app，probe agent post 到这个app

这个app也是一个pod，作为一个service，要打包成docker，写yaml（指定一个worker node），apply过去

yaml 里记得选latest version 不然不会重新pull，mac上打包docker要specify platform

```
docker buildx build --platform linux/amd64 -t yongyuliu03/net-aggregator:v2 --push .
```

## network-aggregator

需要另外配置rbac权限

Deployment 是用来“部署服务”的，Service 是用来“访问服务”的。

network-aggregator Deployment -> 运行 Flask 应用

net-aggregator Service -> 让 probe-agent 能找到 Flask aggregator 的地址

## Deployment vs DaemonSet vs Service

用 Deployment 运行多个相同的业务 Pod（比如 nginx, flask）

用 DaemonSet 在每个节点运行一个系统级 Pod（比如日志、探测器、iperf3 server）

用 Service 把多个 Pod 包装成一个统一网络入口

# kube scheduler 如果要customize scheduler，怎么安装？

克隆并修改 kube-scheduler 源码

(https://kubernetes.io/docs/tasks/extend-kubernetes/configure-multiple-schedulers/)

正常安装kube，和默认scheduler并行

--secure-port=10259 -> 10260

## network scoring function 还要设计

```math
score = w1 * f(RTT) + w2 * f(Bandwidth) + w3 * f(LossRate) \\

f(x) = 100 - normalize(latency) \\

f(y) = log(bandwidth) \\

f(z) = 100 * (1 - lossRate) \\
```

metric - label

RTT: 越低越好 - latency

Bandwidth: 越高越好 - throughput

LossRate: 越低越好 - reliability

权重 （0-1）

Score function 更新

```math
normLatency = latency / maxLatency

normBandwidth = 1 - (bandwidth / maxBandwidth)

normLossrate = lossrate / maxLossrate

cost = latencyWeight * normLatency + bandwidthWeight * normBandwidth + lossrateWeight * normLossrate


total_cost = dependantCost + dependencyCost

score = int64(100 * (1 - cost))

```

```
function Score(pod, candidateNode):
    myApp = pod.app
    myNode = candidateNode
    totalCost = 0

    for each dependency in AppGroup[myApp].dependencies:
        for each replicaNode in GetNodesRunning(dependency):
            cost += weight_latency   × (latency[myNode][replicaNode] / maxLatency)
                  + weight_bandwidth × (1 - bandwidth[myNode][replicaNode] / maxBandwidth)
                  + weight_lossrate × (lossrate[myNode][replicaNode] / maxLossrate)

        avgCost = cost / number of replicas
        totalCost += appWeight[myApp] × avgCost

    score = MAX_SCORE × (1 / (1 + totalCost))
    return score

```

DependencyCost : 我向别人发请求的cost，拉取dependency pod所在node的network cost

DependantCost : 别人向我发请求的cost，反向查询dependant pod 所在的node到被打分的node的network cost

最大值由aggregator提供

# 构建appgroup crd，1 决定pod的部署顺序，2 根据已经部署的pods和待部署的pod的网络条件，决定pod的部署位置 (local optimal and greedy)

ok现在的情况是这样的，我已经可以收集node之间的带宽，rtt，loss rate，我有network topology的crd和get api

为了让pod可以部署在网络环境最好的node上，我们需要先搞清楚pod之间的沟通（哪些服务有依赖？沟通最频繁？），所以我们需要定义一个新的crd叫做app group，里面有service之间的dependency。关于这个我有问题，如果我要deploy这些service，还需要另外怎么apply具体的跑这些服务的docker？怎么和crd联系上？然后如果需要replica要怎么做？

然后我们就该写scheduler plugin，extension point是

1. queuesort，在这里对等待被调度的pod里进行sort，选择应该最先被调度的pod（这里我不是很懂，判断部署顺序的标准是什么？然后如果需要sort的话就说明pod是批量部署的对吧，我理解是一次性部署一个app里的所有services？）

sort的标准是pod之间会不会进行频繁通信，不是业务依赖！

appgroup现在等于通信权重图

2. scoring，对于当前的pod，计算每个node对于pod的打分，哪个node更适合，这里的node的network metric应该怎么使用？是根据已经部署的pod所在的node和当前pod对他们是否有依赖来打分吗？如果根据service依赖打分，会不会导致某个node成为hotspot部署很多pod？

然后遥远的将来如果写出来了，我们需要找合适的workload测试，按照appgroup crd的schema定义这些workload的依赖，部署并测试？

我们还需要设计networkaware有意义的场景，调整vm之间的网络连接情况，使用特殊的workload来跑实验？

设计具有明确通信拓扑的 workload

推荐使用「简化模型」而不是复杂真实业务

- 自己写一组 dummy services，每个服务调用下游 + sleep 模拟延迟
- 用固定模板构造不同结构的服务依赖图：
- 链式（A→B→C）
- 星型（A→B1, B2, B3）
- 双向交叉（A→B←C）

Service Function Chaining
(https://www.sciencedirect.com/science/article/pii/S1084804516301989)

DAG-based Job Scheduling in Kubernetes

## understand kube-scheduler

(https://www.awelm.com/posts/kube-scheduler/)

# kube-scheduler-simulator

(https://github.com/kubernetes-sigs/kube-scheduler-simulator)

# ansible 自动化到其他vm

kubespray

dashboard ui

# 设计networkaware有意义的场景

control network condition: tc

## 模拟workload

## 收集数据

network level
   pod-pod latency RTT | ping, tcptraceroute | ms
   bandwidth | iperf3 | Mbps
   packet loss | ping -c 100 or iperf -u | %
   jitter | ping -Q/iperf -u -b | ms

app level
   response time | curl -w | ms
   QPS | ab -c 10 -n 1000 | QPS
   throughput | ab -c 10 -n 1000 | Mbps
   completion time | ab -c 10 -n 1000 | ms
   error rate | ab -c 10 -n 1000 | %

## benchmark对比


## 三种不同的workload和对应的network topology

online botique app

distributed database cassandra

cloud to edge

外部用户测试端到端延迟


## todo

network plugin修改log，尽量简洁

为三个workload写不同的tc script，先测试，不要一口气跑全部

看faro utility function，看看能否借鉴，优化scoring function，找文献

研究到底收集哪些实验数据，怎么摆实验数据好看，想清楚再写script
