# Helm chart

## Prerequisites

* Make sure you have kubectl [installed](https://kubernetes.io/de/docs/tasks/tools/install-kubectl/).
* Make sure you have Helm [installed](https://helm.sh/docs/using_helm/#installing-helm).
* Make sure you have access to the desired cluster and selected the right namespace

## Deploy Helm chart manually
1. Simply run:

```bash
helm -n <env-namespace> upgrade --install <env-name> . -f values.yaml --set global.image.tag=<image-version>
```

Note: Via the "`--set <variable>=<value>`" parameter every value of the values.yaml can be overriden.
