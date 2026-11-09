# Hands-on kubectl tour

A guided tour through the cluster of this project: from *"what's running?"* to *"break it and watch Kubernetes fix it"*. Every step is a few commands plus what to look for.

**Before you start:** run `make deploy` (see the [README](../README.md)) and use the same terminal for everything below. On Windows, that's your WSL/Ubuntu terminal, because that's where the cluster config lives.

## What `make deploy` created

```
Namespace demo
|-- Deployment hello-app          "I want 3 pods running hello-app:1.0.0"
|   `-- ReplicaSet hello-app-...  one per version; creates and deletes the pods
|       `-- Pod x3                one container each (the image built from app/Dockerfile)
`-- Service hello-app             finds the pods by their label app=hello-app and load-balances across them
```

The definitions live in [`k8s/`](../k8s), the settings (version, replicas, ...) in [`ansible/group_vars/all.yml`](../ansible/group_vars/all.yml).

## 0. Make `demo` your default namespace

```bash
kubectl config set-context --current --namespace=demo   # saves typing "-n demo" on every command
```

## 1. Look around

```bash
kubectl config get-contexts              # the clusters kubectl knows (* = current)
kubectl cluster-info                     # where the API server runs
kubectl get nodes -o wide                # the machines in the cluster (Minikube = 1 node)
kubectl get namespaces                   # demo, default, kube-system, ...
kubectl get all                          # deployment, replicaset, pods and service in "demo"
kubectl get pods -o wide --show-labels   # pod IPs, node and labels
```

## 2. Inspect objects

```bash
kubectl describe deployment hello-app      # strategy and replicas, events at the bottom
kubectl describe pod <pod-name>            # copy a name from "kubectl get pods": probes, IP, events
kubectl get deployment hello-app -o yaml   # the full object as Kubernetes stores it
kubectl explain deployment.spec.strategy.rollingUpdate   # built-in docs for any field
kubectl get events --sort-by=.lastTimestamp              # what happened, in order
```

> In the YAML, compare `spec` with `status`. `spec` is what you asked for: your `k8s/deployment.yaml.j2` plus the defaults Kubernetes filled in. `status` is what is actually running. Kubernetes constantly works to make the two match.

## 3. Logs, and a look inside a pod

```bash
kubectl logs -l app=hello-app --prefix    # logs of all pods (refresh the app in the browser first)
kubectl logs -f deploy/hello-app          # follow one pod live, Ctrl+C to stop
kubectl exec -it deploy/hello-app -- sh   # open a shell inside a running container
```

Inside the container:

```sh
hostname                  # the pod name
env | grep APP_VERSION    # set by the Deployment
cat /etc/resolv.conf      # the cluster's DNS server and search domains
exit
```

## 4. Networking: Service, DNS and endpoints

```bash
kubectl get service hello-app                                         # ClusterIP + NodePort 30080
kubectl get endpointslices -l kubernetes.io/service-name=hello-app   # the pod IPs behind the Service
kubectl run tmp --rm -it --image=busybox:1.36 --restart=Never -- sh  # a throwaway pod to test from
```

Inside busybox:

```sh
nslookup hello-app.demo.svc.cluster.local   # the Service's DNS name resolves to its ClusterIP
wget -qO- http://hello-app/api/info         # run this a few times: different pods answer
exit                                        # the pod deletes itself (--rm)
```

Bonus: `kubectl port-forward svc/hello-app 8080:80` makes the app available at <http://localhost:8080>. Unlike the Service, port-forward always sticks to one pod.

## 5. Watch Kubernetes keep things running

Open a second terminal with `kubectl get pods -w` for a live view, then run these in the first one:

```bash
kubectl delete pod <pod-name>                        # self-healing: a replacement appears within seconds
kubectl scale deployment hello-app --replicas=5      # scale by hand ...
make deploy                                          # ... and back to 3: your files win (declarative config)
kubectl label pod <pod-name> app=debug --overwrite   # take one pod out of the Deployment
kubectl get pods --show-labels                       # a new pod was created; the debug pod keeps running but gets no traffic
kubectl delete pod <pod-name>                        # clean up the pod you relabeled
```

> The Deployment and the Service both find their pods **by label**, not by name. Change the label, and the pod is no longer theirs.

## 6. Rollouts, history and rollbacks

```bash
make deploy VERSION=1.1.0                    # rolling update (watch the -w terminal)
kubectl rollout history deployment/hello-app
kubectl get replicasets                      # the old ReplicaSet is kept with 0 pods ...
kubectl rollout undo deployment/hello-app    # ... which is what makes an instant rollback possible
```

Break it on purpose:

```bash
kubectl set image deployment/hello-app hello-app=hello-app:9.9.9   # an image that doesn't exist
kubectl get pods                      # 1 new pod stuck in ErrImageNeverPull; the old 3 keep serving (maxUnavailable: 0)
kubectl describe pod <broken-pod>     # the Events at the bottom tell you why
kubectl rollout undo deployment/hello-app
```

Afterwards, `make deploy` puts everything back to what's in your files.

## 7. Under the hood

```bash
kubectl get pods -n kube-system        # the control plane: apiserver, etcd, scheduler, controller-manager, coredns, kube-proxy
kubectl describe node minikube         # capacity and reservations ("Allocated resources")
minikube ssh -- sudo crictl ps         # the actual containers running on the node
kubectl get pods -v=6                  # kubectl is just a REST client: see the HTTP calls it makes
kubectl api-resources                  # every kind of object the cluster knows about
minikube addons enable metrics-server  # wait about a minute, then:
kubectl top pods                       # live CPU and memory per pod
minikube dashboard                     # all of this in a web UI
```

## Cheat sheet

| Command | What it does |
|---|---|
| `kubectl get <kind>` | List objects: `pods`, `deploy`, `rs`, `svc`, `nodes`, `all`, ... |
| `kubectl describe <kind> <name>` | Details plus recent events: start here when something is wrong |
| `kubectl get <kind> <name> -o yaml` | The full object, including its status |
| `kubectl logs <pod>` (`-f` to follow) | The logs of a container |
| `kubectl exec -it <pod> -- sh` | A shell inside a container |
| `kubectl apply -f <file>` | Create or update objects from a file (declarative) |
| `kubectl delete <kind> <name>` | Delete an object |
| `kubectl scale deploy <name> --replicas=<n>` | Change the number of pods |
| `kubectl rollout status\|history\|undo deploy/<name>` | Follow, list or roll back updates |
| `kubectl port-forward svc/<name> 8080:80` | Reach a service from your machine |
| `kubectl explain <kind>.<field>` | Built-in docs for any field |

## Clean up

```bash
kubectl config set-context --current --namespace=default   # back to the normal default namespace
make destroy                                               # remove the app (Minikube keeps running)
```

## Ideas to explore next

- Move `APP_VERSION` into a **ConfigMap** and mount it into the pods.
- Scale automatically with a **HorizontalPodAutoscaler** (needs the metrics-server from step 7).
- Expose the app under a hostname with an **Ingress** (`minikube addons enable ingress`).
