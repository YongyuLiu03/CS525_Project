
# introduction of relative work

## 0. K8s

## 1. K8s scheduler
In Kubernetes, scheduling refers to making sure that Pods are matched to Nodes so that the kubelet can run them. Preemption is the process of terminating Pods with lower Priority so that Pods with higher Priority can schedule on Nodes. Eviction is the process of terminating one or more Pods on Nodes.


The Kubernetes scheduler is a control plane process which assigns Pods to Nodes. The scheduler determines which Nodes are valid placements for each Pod in the scheduling queue according to constraints and available resources. The scheduler then ranks each valid Node and binds the Pod to a suitable Node. Multiple different schedulers may be used within a cluster; kube-scheduler is the reference implementation. See scheduling for more information about scheduling and the kube-scheduler component.


## 2. CRD

## 3. scheduler scoring function

## 优势

first network aware scheduler in k8s

轻量级的scheduler插件

## CRD vs Aggregation layer api

introduce both and choose CRD

## local optimal + greedy vs "global optimal"


# Discussion

## DeamonSet Trade off and comsumption

