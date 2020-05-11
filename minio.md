# Using Minio as storage layer

0. Install [Helm](https://helm.sh/) and add the offical stable charts. You can think of Helm as a package manager for Kubernetes.
```
brew install helm
helm repo add stable https://kubernetes-charts.storage.googleapis.com/
```

1. Configure the cluster to enable Argo artifacts using [Minio](https://min.io/) as a storage layer.

```bash
helm install argo-artifacts stable/minio \
  --set service.type=LoadBalancer \
  --set defaultBucket.enabled=true \
  --set defaultBucket.name=my-bucket \
  --set persistence.enabled=false \
  --set fullnameOverride=argo-artifacts
```

Find the URL for the Minio UI:
```bash
minikube service --url argo-artifacts
```

Copy and paste it into your browser. You should see a login screen, enter the following credentials. After logging in, you should see a bucket named `my-bucket`:

* AccessKey: AKIAIOSFODNN7EXAMPLE
* SecretKey: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

Finally, enable the workflow controller to use Minio. Open the config map with `kubectl edit cm -n argo workflow-controller-configmap`, then add the following lines at the bottom:
```yaml
data:
  config: |
    artifactRepository: |
      s3:
        bucket: my-bucket
        endpoint: argo-artifacts.default:9000
        insecure: true
        # accessKeySecret and secretKeySecret are secret selectors.
        # It references the k8s secret named 'argo-artifacts'
        # which was created during the minio helm install. The keys,
        # 'accesskey' and 'secretkey', inside that secret are where the
        # actual minio credentials are stored.
        accessKeySecret:
          name: argo-artifacts
          key: accesskey
        secretKeySecret:
          name: argo-artifacts
          key: secretkey
```
