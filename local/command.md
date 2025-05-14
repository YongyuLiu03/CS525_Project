# K8s system setup

## All node

create a configuration file (as the root user on each node) to ensure these modules load at system boot:

```bash
    sudo tee /etc/modules-load.d/kubernetes.conf > /dev/null <<EOF
    br_netfilter
    ip_vs
    ip_vs_rr
    ip_vs_wrr
    ip_vs_sh
    overlay
    EOF
```

To set specific sysctl settings (on each node) that Kubernetes relies on, you can update the system’s kernel parameters. These settings ensure optimal performance and compatibility for Kubernetes. Here’s how you can configure the necessary sysctl settings:

```bash
    sudo tee /etc/sysctl.d/kubernetes.conf << EOF
    net.ipv4.ip_forward = 1
    net.bridge.bridge-nf-call-ip6tables = 1
    net.bridge.bridge-nf-call-iptables = 1
    EOF
```

After creating the configuration file, apply the sysctl settings immediately without rebooting:

```bash
    sudo sysctl --system
```

Disable swap

```bash
    sudo swapoff -a
    sudo sed -e '/swap/s/^/#/g' -i /etc/fstab
```

Install containerd

```bash
    sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    sudo dnf makecache
    sudo dnf -y install containerd.io
```

Configure containerd, SystemdCgroup = false

```bash
    sudo containerd config default | sudo tee /etc/containerd/config.toml
    sudo sh -c "containerd config default > /etc/containerd/config.toml" ; cat /etc/containerd/config.toml
```

Start and enable containerd upon reboot

```bash
    sudo systemctl enable --now containerd.service
    sudo systemctl reboot
    sudo systemctl status containerd.service
```

Firewall

```bash

    sudo firewall-cmd --zone=public --permanent --add-port=6443/tcp
    sudo firewall-cmd --zone=public --permanent --add-port=2379-2380/tcp
    sudo firewall-cmd --zone=public --permanent --add-port=10250/tcp
    sudo firewall-cmd --zone=public --permanent --add-port=10251/tcp
    sudo firewall-cmd --zone=public --permanent --add-port=10252/tcp
    sudo firewall-cmd --zone=public --permanent --add-port=10255/tcp
    sudo firewall-cmd --zone=public --permanent --add-port=5473/tcp
    sudo firewall-cmd --reload

```

Kubernetes

```bash
    cat <<EOF | sudo tee /etc/yum.repos.d/kubernetes.repo
    [kubernetes]
    name=Kubernetes
    baseurl=https://pkgs.k8s.io/core:/stable:/v1.32/rpm/
    enabled=1
    gpgcheck=1
    gpgkey=https://pkgs.k8s.io/core:/stable:/v1.32/rpm/repodata/repomd.xml.key
    exclude=kubelet kubeadm kubectl cri-tools kubernetes-cni
    EOF

    sudo dnf makecache 
    sudo dnf install -y kubelet kubeadm kubectl --disableexcludes=kubernetes

    sudo systemctl enable --now kubelet.service 
```

## master node

```bash
    sudo kubeadm config images pull
    sudo kubeadm init --pod-network-cidr=10.244.0.0/16
```

```bash
    mkdir -p $HOME/.kube
    sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
    sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

CNI (Calico, v3.29.3)

```bash
    kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.29.3/manifests/tigera-operator.yaml
    curl -O https://raw.githubusercontent.com/projectcalico/calico/v3.29.3/manifests/custom-resources.yaml
    sed -i 's/cidr: 192\.168\.0\.0\/16/cidr: 10.244.0.0\/16/g' custom-resources.yaml
    kubectl create -f custom-resources.yaml
```

## worker node

```bash
sudo kubeadm join 172.22.153.61:6443 --token hz68a0.4w7dpy643ltlwa3h --discovery-token-ca-cert-hash sha256:8535be410d9b8ecd68320e1d22fa6b040953e9e5dbcbb0cc25d5db03bf5ceab5 
```

## install iperf3

```bash
	sudo yum install epel-release -y
    sudo yum install iperf3 -y
```

## apply iperf3 and network-probe-agent daemonset

```bash
    kubectl apply -f iperf3-server.yaml
    kubectl get pods -n kube-system -l app=iperf3-server -o wide


    kubectl apply -f network-probe-agent.yaml

    kubectl get pods -n kube-system -l app=network-probe-agent -o wide

```

## apply network-aggregator

```bash
    kubectl apply -f network-aggregator.yaml
    kubectl get pods -n kube-system -l app=net-aggregator -o wide
```

## apply crd

```bash
    kubectl apply -f networktopology-crd.yaml
    kubectl get crd | grep networktopologies
    kubectl apply -f networktopology-sample.yaml
    kubectl get networktopology
```

## 检查正常运行

```bash
    kubectl get networktopology cluster-network -o yaml --watch
    kubectl get svc net-aggregator -n kube-system
    kubectl logs -l app=net-aggregator -n kube-system -f
    kubectl get pods -l app=network-probe-agent -n kube-system
    kubectl logs -n kube-system -l app=network-probe-agent -f

```

appgroup-controller → 10.108.70.16

net-aggregator      → 10.104.60.124

# kube-scheduler

```bash
    kubectl get pods -n kube-system -l component=kube-scheduler
    kubectl logs -n kube-system <scheduler-pod-name>
```


# enable netem module
```bash
    sudo yum install kernel-modules-extra
    sudo modprobe sch_netem
    
```