# ENCODE demo-pipeline with Kubeflow Pipelines

In this guide you will walk through running the demo pipeline on a local single node Kubernetes cluster using [Kubeflow Pipelines](https://www.kubeflow.org/docs/pipelines/). Under the hood, it relies on [Argo](https://argoproj.github.io/) to execute the workflow. However, there is also a 

## Install kubectl, minikube, and Kubeflow Pipelines

The following instructions are for MacOS users, although the general proceduce should be similar on other platforms. The Kubeflow Pipelines standalone deployment process is adapted from https://github.com/kubeflow/pipelines/tree/master/manifests/kustomize#option-1-install-it-to-any-k8s-cluster . If you have already installed `kubectl` and `minikube`, as in the Argo example, you can skip steps 0 and 1.

System requirements:
  * [Docker CE](https://docs.docker.com/install/)
  * Python 3.5 or greater
  * [brew](https://brew.sh) for installing packages (MacOS only)

0. Install [kubectl](https://kubernetes.io/docs/tasks/tools/install-minikube/) and verify it:
```bash
brew install kubectl
kubectl version --client
```

1. Install [minikube](https://kubernetes.io/docs/tasks/tools/install-minikube/), start the cluster, and verify that the cluster is up. If you have `Docker` installed, you should have `hyperkit` available, you can verify with `hyperkit -h` . This will NOT work with Kubernetes 1.18
```bash
brew install minikube
minikube start \
    --kubernetes-version=v1.17.0 \
    --cpus 6 \
    --memory 12288 \
    --disk-size=120g \
    --extra-config=kubelet.resolv-conf=/run/systemd/resolve/resolv.conf \
    --extra-config kubeadm.ignore-preflight-errors=SystemVerification
minikube status
```

* Note: if you already have previously run `minikube` and experience errors after starting the cluster, try running the following:
```bash
minikube stop
minikube delete
```

2. Create a persistent volume:
```bash
kubectl apply -f hostpath-pv.yaml
```

3. Install Kubeflow Pipelines and launch expose the UI at http://localhost:8080:
```bash
export PIPELINE_VERSION=0.5.1
kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/cluster-scoped-resources?ref=$PIPELINE_VERSION"
kubectl wait crd/applications.app.k8s.io --for condition=established --timeout=60s
kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/env/platform-agnostic/?ref=$PIPELINE_VERSION"
kubectl wait applications/pipeline -n kubeflow --for condition=Ready --timeout=1800s
kubectl port-forward -n kubeflow svc/ml-pipeline-ui 8080:80
```

This can take quite some time due to the number of containers. You can check the status of the pods with `kubectl get pods -n kubeflow`. Once they are ready, launch and go to the UI.

Note: with Kubernetes 1.18, I experience errors starting the `cache-deployer-deployment` pod and it enters `CrashLoopBackOff` . I would recommend using 1.17 or lower.

## Running pipelines

4. From the UI, run one of the examples to verify that the install is working.

## Set up Python environment for Kubeflow Pipelines SDK

1. Create a Python virtual environment and install the SDK:

```bash
python -m venv venv
source venv/bin/activate/
(venv) pip install -r requirements.txt
```

## Run a toy NGS workflow

5. Upload the test data to the `minio` repository. First expose the UI service:

```bash
kubectl port-forward -n kubeflow svc/minio-service 9000:9000
```

Go to http://localhost:9000 in your browser and login with username `minio` and password `minio123`

6. Now that we have all the pieces in place, we can run our toy workflow. Once again, run these from the `argo` directory in this repo:

```bash
argo submit toy.yaml --parameter-file toy_input.yaml
```

Because we mounted the `data` folder, you will see the `png` plots outputted there.

## Conclusion

🎉 Congrats! You made it to the end of this example.
