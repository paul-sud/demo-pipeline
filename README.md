# ENCODE demo-pipeline with Argo

**For demonstration purposes only, NOT production grade**

See [ENCODE's original repo](https://github.com/ENCODE-DCC/demo-pipeline) for details on what the pipeline does. We will focus here on the mechanics of running the pipeline using [Argo](https://argoproj.github.io/), a [Kubernetes](https://kubernetes.io/)-native workflow execution system.

# Guide

## Install kubectl, minikube, Argo, and Helm

The following instructions are for MacOS users, although the general proceduce should be similar on other platforms. The Argo setup process is copied from https://argoproj.github.io/docs/argo/getting-started.html .

System requirements:
  * [Docker CE](https://docs.docker.com/install/)
  * [brew](https://brew.sh) for installing packages

0. Install [kubectl](https://kubernetes.io/docs/tasks/tools/install-minikube/) and verify it:
```bash
brew install kubectl
kubectl version --client
```

1. Install [minikube](https://kubernetes.io/docs/tasks/tools/install-minikube/), start the cluster, and verify that the cluster is up. If you have `Docker` installed, you should have `hyperkit` available, you can verify with `hyperkit -h`
```bash
brew install minikube
minikube start --driver=hyperkit
minikube status
```

2. Install the [Argo](https://argoproj.github.io/) CLI, install the Argo controller on the cluster, and create an admin role in the argo namespace:
```bash
brew install argoproj/tap/argo
kubectl create namespace argo
kubectl apply -n argo -f https://raw.githubusercontent.com/argoproj/argo/stable/manifests/install.yaml
kubectl create rolebinding default-admin --clusterrole=admin --serviceaccount=default:default
```

3. (Optional, highly recommended) In another terminal window, start the Argo UI. Once it starts, you can visit the UI at http://127.0.0.1:2746/workflows
```bash
kubectl -n argo port-forward deployment/argo-server 2746:2746
```

* Note: if you've previously stopped the cluster, you can bring the server up again simply with `argo server`

4. To test your Argo install, run some toy workflows. You can view them as they run on the UI or monitor them on the command line:
```bash
argo submit --watch https://raw.githubusercontent.com/argoproj/argo/master/examples/hello-world.yaml
argo submit --watch https://raw.githubusercontent.com/argoproj/argo/master/examples/coinflip.yaml
```

## Run a toy NGS workflow

5. To run a workflow with persistent data, we could either use Argo artifacts or a Kubernetes PersisentVolume (PV). Artifacts work better for Argo, since they do nice things like automatically convert directories to tarballs, and automatically perform gzip compression and are in general easier to work with.

Here we will use a PV since it doesn't require an account with a cloud storage provider. To get a feel of how volumes work, create a PersistentVolumeClaim (PVC) and run a test workflow using the PVC:

```bash
kubectl create -f https://raw.githubusercontent.com/argoproj/argo/master/examples/testvolume.yaml
argo submit https://raw.githubusercontent.com/argoproj/argo/master/examples/volumes-existing.yaml
```

To create something we can use to pass in the input data, we can create a ReadOnlyMany (ROX) persistent volume. Edit the file `hostpath-volume.yaml` to point to where the test data is on your system, then create the PersistentVolume and PVC. We also need to make the test data in this repo accessible from the Kubernetes Node.

Open another terminal window, `cd` to the repo root, and run the following to mount the test data:

```bash
minikube mount $PWD/demo-pipeline/data:/mnt/data
```

You can verify the presence of the data by SSHing onto the node with `minikube ssh` and `ls`ing `/mnt/data`. Next, create the PersistentVolume and PersistentVolumeClaim resources:

```bash
kubectl apply -f hostpath-volume.yaml
kubectl apply -f hostpath-pvc.yaml
```

6. Now that we have all the pieces in place, we can run our toy workflow.

```bash
argo submit toy.yaml --parameter-file toy_input.yaml
```

Because we mounted the `data` folder, you will see the `png` plots outputted there.

## Conclusion

🎉 Congrats! You made it to the end of this example. Hopefully you are now a little more familiar with Argo workflows and how it works with Kubernetes. For more reading, check out the [Argo examples](https://github.com/argoproj/argo/tree/master/examples), there are a lot of features we didn't cover here.
