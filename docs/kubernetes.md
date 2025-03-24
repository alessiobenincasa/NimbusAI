# Configuration Kubernetes du Chatbot LLM

Ce document explique en détail la configuration Kubernetes utilisée pour déployer notre chatbot LLM.

## Architecture Kubernetes

Notre application est déployée sur Kubernetes avec la configuration suivante:

```
                            ┌───────────────┐
                            │  INGRESS      │
                            │  CONTROLLER   │
                            └───────┬───────┘
                                    │
                 ┌──────────────────┼───────────────────┐
                 │                  │                   │
        ┌────────▼─────────┐ ┌──────▼──────────┐ ┌─────▼──────────┐
        │   NAMESPACE:     │ │   NAMESPACE:    │ │   NAMESPACE:   │
        │      APP         │ │   MONITORING    │ │     GITLAB     │
        └──────────────────┘ └─────────────────┘ └────────────────┘
                 │                  │                   │
     ┌───────────┼──────────┐       │                   │
     │           │          │       │                   │
┌────▼───┐  ┌────▼───┐ ┌────▼───┐   │              ┌────▼────┐
│ API    │  │  LLM   │ │DATABASE│   │              │ GITLAB  │
│SERVICE │  │SERVICE │ │STATEFUL│   │              │   CI    │
└────────┘  └────────┘ └────────┘   │              └─────────┘
                                     │
                         ┌───────────┼───────────┐
                         │           │           │
                     ┌───▼───┐   ┌───▼───┐   ┌───▼───┐
                     │GRAFANA│   │PROMETH│   │  ELK  │
                     │       │   │  EUS  │   │ STACK │
                     └───────┘   └───────┘   └───────┘
```

## Namespaces

Nous utilisons trois namespaces pour isoler les différentes parties de notre système:

1. **app**: Contient les composants de l'application (API, LLM Service, Database)
2. **monitoring**: Contient les outils de monitoring (Prometheus, Grafana, ELK)
3. **gitlab**: Contient les composants CI/CD (GitLab, GitLab Runner)

```yaml
# k8s/namespaces.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: app
  labels:
    name: app
    environment: production
---
apiVersion: v1
kind: Namespace
metadata:
  name: monitoring
  labels:
    name: monitoring
    environment: production
---
apiVersion: v1
kind: Namespace
metadata:
  name: gitlab
  labels:
    name: gitlab
    environment: production
```

## Classes de stockage

Nous utilisons une classe de stockage local pour le développement:

```yaml
# k8s/storage-class.yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: local-storage
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: k8s.io/minikube-hostpath
volumeBindingMode: Immediate
reclaimPolicy: Delete
```

En production, cette classe de stockage serait remplacée par une option plus robuste comme:
- AWS EBS
- Azure Disk
- Google Persistent Disk
- Une solution de stockage distribuée (Longhorn, Rook-Ceph)

## Déploiement de l'API

L'API est déployée avec un Deployment Kubernetes:

```yaml
# k8s/api/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-chatbot-api
  namespace: app
spec:
  replicas: 3  # 3 réplicas pour la haute disponibilité
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0  # Garantit zéro downtime
  selector:
    matchLabels:
      app: llm-chatbot
      component: api
  template:
    metadata:
      labels:
        app: llm-chatbot
        component: api
      annotations:
        prometheus.io/scrape: "true"  # Permet à Prometheus de scraper les métriques
    spec:
      containers:
      - name: api
        image: localhost:5000/llm-chatbot-api:${VERSION}
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:  # Secret pour les credentials DB
              name: database-credentials
              key: url
        - name: LLM_SERVICE_URL
          value: "http://llm-chatbot-llm:8001"
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
        readinessProbe:  # Vérifie que le pod est prêt à recevoir du trafic
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:  # Vérifie que le pod est vivant
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 15
          periodSeconds: 20
```

## Déploiement du Service LLM

Le service LLM est également déployé via un Deployment:

```yaml
# k8s/llm/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-chatbot-llm
  namespace: app
spec:
  replicas: 2  # Moins de réplicas car plus exigeant en ressources
  strategy:
    type: RollingUpdate
  selector:
    matchLabels:
      app: llm-chatbot
      component: llm
  template:
    metadata:
      labels:
        app: llm-chatbot
        component: llm
    spec:
      containers:
      - name: llm
        image: localhost:5000/llm-chatbot-llm:${VERSION}
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2
            memory: 4Gi  # Plus de mémoire pour le modèle LLM
        volumeMounts:
        - name: models-volume
          mountPath: /app/models  # Montage du volume pour les modèles
      volumes:
      - name: models-volume
        persistentVolumeClaim:
          claimName: llm-models-pvc  # Stockage persistant pour les modèles
```

## Base de données StatefulSet

La base de données est déployée via un StatefulSet pour garantir la persistance des identifiants:

```yaml
# k8s/database/deployment.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: llm-chatbot-database
  namespace: app
spec:
  serviceName: "llm-chatbot-database"
  replicas: 1  # Une seule réplica en dev, possibilité d'ajouter des réplicas de lecture
  selector:
    matchLabels:
      app: llm-chatbot
      component: database
  template:
    metadata:
      labels:
        app: llm-chatbot
        component: database
    spec:
      containers:
      - name: postgres
        image: localhost:5000/llm-chatbot-database:${VERSION}
        env:
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: password
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data  # Montage du stockage persistant
  volumeClaimTemplates:  # Demande de volume persistant
  - metadata:
      name: postgres-data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: "local-storage"
      resources:
        requests:
          storage: 10Gi
```

## Ingress Controller

L'Ingress Controller gère le routage du trafic entrant:

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: llm-chatbot-ingress
  namespace: app
  annotations:
    kubernetes.io/ingress.class: "nginx"
    nginx.ingress.kubernetes.io/rewrite-target: /$2  # Réécriture des paths
spec:
  rules:
  - http:
      paths:
      - path: /api(/|$)(.*)  # Tous les chemins /api/* vont à l'API
        pathType: Prefix
        backend:
          service:
            name: llm-chatbot-api
            port:
              number: 80
      - path: /llm(/|$)(.*)  # Tous les chemins /llm/* vont au service LLM
        pathType: Prefix
        backend:
          service:
            name: llm-chatbot-llm
            port:
              number: 8001
```

## Configuration du monitoring

Le monitoring est configuré avec Prometheus et Grafana:

```yaml
# Exemple simplifié de monitoring/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
```

## Secrets

Les secrets comme les credentials de base de données sont stockés de manière sécurisée:

```yaml
# k8s/database/deployment.yaml (extrait)
apiVersion: v1
kind: Secret
metadata:
  name: database-credentials
  namespace: app
type: Opaque
data:
  username: cG9zdGdyZXM=  # Base64 pour "postgres"
  password: cG9zdGdyZXM=  # Base64 pour "postgres"
  url: cG9zdGdyZXNxbDovL3Bvc3RncmVzOnBvc3RncmVzQGxsbS1jaGF0Ym90LWRhdGFiYXNlOjU0MzIvbGxtY2hhdGJvdA==  # Base64 pour l'URL complète
```

## Bonnes pratiques utilisées

Notre configuration Kubernetes suit plusieurs bonnes pratiques:

1. **Zero-Downtime Deployments**:
   - RollingUpdate avec maxUnavailable: 0
   - Readiness probes configurées correctement

2. **Resource Management**:
   - Limits et requests définis pour tous les containers
   - Évite l'over-commitment des ressources

3. **Health Checks**:
   - Liveness probes pour redémarrer les containers défectueux
   - Readiness probes pour contrôler le trafic

4. **Sécurité**:
   - Secrets pour les données sensibles
   - Namespaces pour l'isolation

5. **Observabilité**:
   - Annotations pour le scraping Prometheus
   - Métriques exportées par les services

6. **Persistence**:
   - PersistentVolumeClaims pour les données persistantes
   - StatefulSet pour la base de données

## Conclusion

Cette configuration Kubernetes offre une plateforme robuste, évolutive et observable pour notre application de chatbot LLM, tout en suivant les bonnes pratiques DevOps pour garantir une fiabilité élevée et une maintenance facilitée. 