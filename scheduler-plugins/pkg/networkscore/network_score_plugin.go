// network_score_plugin.go
package networkscore

import (
	"context"
	"encoding/json"
	// "fmt"
	"net/http"
	"strings"
	// "k8s.io/apimachinery/pkg/labels"
	"k8s.io/klog/v2"
	v1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/runtime"
	framework "k8s.io/kubernetes/pkg/scheduler/framework"
	"math"
)

const (
	PluginName          = "NetworkAwareScore"
	AppGroupGraphAPI    = "http://10.108.70.16:8090/graph/"
	NetworkTopologyAPI  = "http://10.104.60.124:8080/topology"
	MaxNodeScore      = 100
	SameNodeScore    = 0.8
	UnreachableNodeScore = 0
	NoDependencyDefaultScore = 0
)

type NetworkScorePlugin struct {
	handle framework.Handle
}

type TopologyData struct {
    Latency map[string]map[string]float64 `json:"latency"`
    Bandwidth map[string]map[string]float64 `json:"bandwidth"`
    Lossrate map[string]map[string]float64 `json:"lossrate"`
    MaxLatency float64 `json:"maxLatency"`
    MaxBandwidth float64 `json:"maxBandwidth"`
    MaxLossrate float64 `json:"maxLossrate"`
	MinLatency    float64 `json:"minLatency"`
	MinBandwidth  float64 `json:"minBandwidth"`
	MinLossrate   float64 `json:"minLossrate"`
}


type GraphData map[string]struct {
	Weight	  float64 `json:"weight"`
	Dependencies map[string]map[string]float64 `json:"dependencies"`
}


var _ framework.ScorePlugin = &NetworkScorePlugin{}

func (pl *NetworkScorePlugin) Name() string {
	return PluginName
}

func New(ctx context.Context, obj runtime.Object, handle framework.Handle) (framework.Plugin, error) {
	return &NetworkScorePlugin{handle: handle}, nil
}

func (pl *NetworkScorePlugin) Score(ctx context.Context, state *framework.CycleState, pod *v1.Pod, nodeName string) (int64, *framework.Status) {
	appgroup := pod.Labels["appgroup"]

	if appgroup == "" {
		return 0, framework.NewStatus(framework.Error, "missing app label")
	}

	graphResp, err := http.Get(AppGroupGraphAPI + appgroup)
	if err != nil {
		return 0, framework.NewStatus(framework.Error, "failed to fetch appgroup graph")
	}
	defer graphResp.Body.Close()

	// klog.Infof("[Score] Successfully fetched AppGroup graph for appgroup=%s", appgroup)

	topologyResp, err := http.Get(NetworkTopologyAPI)
	if err != nil {
		return 0, framework.NewStatus(framework.Error, "failed to fetch topology")
	}
	defer topologyResp.Body.Close()
	// klog.Infof("[Score] Successfully fetched NetworkTopology")

	var graph GraphData

	if err := json.NewDecoder(graphResp.Body).Decode(&graph); err != nil {
		return 0, framework.NewStatus(framework.Error, "invalid appgroup graph format")
	}

	var topology TopologyData

	if err := json.NewDecoder(topologyResp.Body).Decode(&topology); err != nil {
		return 0, framework.NewStatus(framework.Error, "invalid topology format")
	}

	thisNode := nodeName
	myApp := pod.Labels["app"]
	myWeight := graph[myApp].Weight

	scoreSum := 0.0 
	totalWeight := 0.0

	// klog.Infof("[Score] Scoring pod app %s", myApp)

	for dep, metrics := range graph[myApp].Dependencies {

		depNodes := findTargetNodes(pl, dep)
		// klog.Infof("[Score] Found %d replicas for dependency app=%s", len(depNodes), dep)

		if len(depNodes) == 0 {
			continue
		}
		inter_Score := 0.0
		for _, targetNode := range depNodes {
			inter_Score += computeScore(thisNode, targetNode, metrics, topology)
		}
		avgScore := inter_Score / float64(len(depNodes))
		scoreSum += myWeight * avgScore
		totalWeight += myWeight
		// klog.Infof("[Score] Updated scoreSum for dependency app=%s: %f", dep, scoreSum)
	}


	dependents := findAllDependents(pl, myApp, appgroup, graph)

	for otherApp := range dependents {
		metrics := graph[otherApp].Dependencies[myApp]
		otherWeight := graph[otherApp].Weight

		replicaNodes := findTargetNodes(pl, otherApp)
		// klog.Infof("[Score] Found %d replicas for dependent app=%s", len(replicaNodes), otherApp)
		
		if len(replicaNodes) == 0 {
			continue
		}

		inter_Score := 0.0
		for _, replicaNode := range replicaNodes {
			inter_Score += computeScore(replicaNode, thisNode, metrics, topology)
		}
		avgScore := inter_Score / float64(len(replicaNodes))
		scoreSum += otherWeight * avgScore
		totalWeight += otherWeight
		// klog.Infof("[Score] Updated scoreSum for dependent app=%s: %f", otherApp, scoreSum)
	}

	var finalScore int64

	if totalWeight == 0.0 {
		finalScore = int64(NoDependencyDefaultScore)
		klog.Infof("[Score] Pod %s has no dependency or reverse dependency; assigning default score", pod.Name)
	} else {
		finalScore = int64(math.Round(scoreSum * MaxNodeScore / totalWeight))
	}

	klog.Infof("[Score] Pod %s, Node %s, FinalScore=%d", pod.Name, shortName(nodeName), finalScore)
	
	return finalScore, framework.NewStatus(framework.Success, "")
}


func computeScore(src, dst string, metrics map[string]float64, topo TopologyData) float64 {
	score := 0.0
	missing := true

	if src == dst {
		score += SameNodeScore
	} else {

		if val, ok := metrics["latency"]; ok {
			if lat, exists := topo.Latency[src][dst]; exists {
				lat = clamp(lat, topo.MinLatency, topo.MaxLatency)
				normRTT := (topo.MaxLatency - lat) / (topo.MaxLatency - topo.MinLatency)
				score += val * normRTT
				missing = false
			}
		}

		if val, ok := metrics["bandwidth"]; ok {
			if bw, exists := topo.Bandwidth[src][dst]; exists && bw > 0 {
				bw = clamp(bw, topo.MinBandwidth, topo.MaxBandwidth)
				normBW := (math.Log(bw) - math.Log(topo.MinBandwidth)) / (math.Log(topo.MaxBandwidth) - math.Log(topo.MinBandwidth))
				score += val * normBW
				missing = false
			}
		}

		if val, ok := metrics["lossrate"]; ok {
			if lr, exists := topo.Lossrate[src][dst]; exists {
				loss := clamp(lr, topo.MinLossrate, topo.MaxLossrate)
				normLoss := (topo.MaxLossrate - loss) / (topo.MaxLossrate - topo.MinLossrate)
				score += val * normLoss
				missing = false
			}
		}

		if missing {
			score += UnreachableNodeScore
		}
	}

	// klog.Infof("[Score] src=%s, dst=%s, latency=%f, bandwidth=%f, lossrate=%f", shortName(src), shortName(dst), topo.Latency[src][dst], topo.Bandwidth[src][dst], topo.Lossrate[src][dst])
	// klog.Infof("[Score] Cost for src=%s, dst=%s: %f", shortName(src), shortName(dst), score)
	return score
}


func findTargetNodes(pl *NetworkScorePlugin, depApp string) []string {
	nodes, err := pl.handle.SnapshotSharedLister().NodeInfos().List()
	if err != nil {
		klog.Errorf("Error getting node info: %v", err)
		return nil
	}

	var result []string
	for _, nodeInfo := range nodes {
		for _, podInfo := range nodeInfo.Pods {
			p := podInfo.Pod
			if p.Labels["app"] == depApp && p.Spec.NodeName != "" {
				result = append(result, p.Spec.NodeName)
			}
		}
	}
	return result
}


func findAllDependents(pl *NetworkScorePlugin, myApp string, myAppGroup string, graph GraphData) map[string]string {
	result := make(map[string]string)
	nodes, err := pl.handle.SnapshotSharedLister().NodeInfos().List()
	if err != nil {
		klog.Errorf("Error getting node info: %v", err)
		return nil	
	}

	for _, nodeInfo := range nodes {
		for _, podInfo := range nodeInfo.Pods {
			p := podInfo.Pod
			appGroup := p.Labels["appgroup"]
			app := p.Labels["app"]
			if appGroup != myAppGroup || app == "" || p.Spec.NodeName == "" {
				continue
			}
			if deps, exists := graph[app].Dependencies[myApp]; exists && deps != nil {
				result[app] = p.Spec.NodeName
			}
		}
	}
	return result
}


func shortName(full string) string {
    parts := strings.Split(full, "-")
    if len(parts) > 0 {
        lastPart := parts[len(parts)-1]
        dotParts := strings.Split(lastPart, ".")
        return dotParts[0]
    }
    return full
}


func clamp(val, min, max float64) float64 {
	if val < min {
		return min
	}
	if val > max {
		return max
	}
	return val
}

func (pl *NetworkScorePlugin) ScoreExtensions() framework.ScoreExtensions {
	return nil
}