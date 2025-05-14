# Extract Default Scheduler Scores

## Step-by-step to enable verbose logging:

1. SSH into your master node.

2. Edit `/etc/kubernetes/manifests/kube-scheduler.yaml`.

3. In the `command` section, add:

    ```yaml
    - --v=5
    ```

4. Save and exit. Kubelet will auto-reload the static Pod.

5. View logs:

    ```bash
    kubectl logs -n kube-system -l component=kube-scheduler
    ```

6. Look for log lines like:

    ```
    "Evaluated node sp25-cs525-1403.cs.illinois.edu for pod frontend-x, score: 85"
    ```

7. Optional: Pipe to grep:

    ```bash
    kubectl logs -n kube-system -l component=kube-scheduler | grep "score:"
    ```

