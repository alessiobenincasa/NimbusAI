# Architecture DevOps du Chatbot LLM

## Vue d'ensemble

Notre architecture DevOps pour le chatbot LLM est conçue pour être hautement évolutive, résiliente et maintenable. Elle suit les principes des architectures cloud-native modernes et implémente les meilleures pratiques DevOps.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              UTILISATEURS                                │
└───────────────────────────────────┬─────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              INGRESS NGINX                               │
└───────────┬─────────────────────────┬─────────────────────────┬─────────┘
            │                         │                         │
            ▼                         ▼                         ▼
┌───────────────────┐     ┌─────────────────────┐    ┌────────────────────┐
│   API SERVICE     │     │    MONITORING       │    │      GITLAB CI     │
│  ┌─────────────┐  │     │  ┌─────────────┐    │    │  ┌──────────────┐  │
│  │   PODS (3)  │◄─┼────►│  │ PROMETHEUS  │    │    │  │   GITLAB     │  │
│  └─────────────┘  │     │  └─────────────┘    │    │  └──────────────┘  │
└─────────┬─────────┘     │  ┌─────────────┐    │    │  ┌──────────────┐  │
          │               │  │   GRAFANA   │    │    │  │GITLAB RUNNER │  │
          ▼               │  └─────────────┘    │    │  └──────────────┘  │
┌─────────────────┐       │  ┌─────────────┐    │    └────────────────────┘
│   LLM SERVICE   │       │  │     ELK     │    │
│  ┌─────────────┐│       │  └─────────────┘    │
│  │   PODS (2)  ││       └─────────────────────┘
│  └─────────────┘│
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│   DATABASE      │
│  ┌─────────────┐│
│  │POSTGRESQL   ││
│  └─────────────┘│
└─────────────────┘
```

## Composants de l'architecture

### 1. Application (couche business)

**API Service**:
- Développé avec FastAPI (Python)
- Exposé via un Ingress Nginx
- Configuré avec autoscaling horizontal (3 pods par défaut)
- Communicating with LLM service via internal service discovery

**LLM Service**:
- Service d'inférence basé sur LangChain et HuggingFace
- Optimisé pour le traitement des LLM en local (sans dépendance externe)
- Persistence des modèles via PersistentVolumeClaims
- Métriques d'inférence exportées vers Prometheus

**Base de données**:
- PostgreSQL en mode StatefulSet
- Backups automatisés
- Haute disponibilité configurable

### 2. Infrastructure (couche technique)

**Kubernetes (K3s)**:
- Orchestration légère des conteneurs
- Isolation par namespaces (app, monitoring, gitlab)
- Ressources limitées et requêtes configurées
- Health checks et readiness probes
- Déploiements progressive (rolling updates)
- Stratégie de rollback automatique

**Ingress Controller**:
- Nginx pour la terminaison SSL et le routage
- Configuration de rate limiting
- Gestion des chemins d'API

**Persistent Storage**:
- Classes de stockage pour différents besoins
- Volumes persistants pour les données critiques

### 3. CI/CD

**GitLab CI**:
- Pipeline automatisé en 4 étapes: Test, Build, Deploy, Monitor
- Auto-hébergé pour éviter les dépendances externes
- Registre Docker local
- Cache d'artefacts

**Pipeline**:
- Tests automatisés (unitaires, intégration)
- Construction d'images Docker avec versionnement
- Déploiement immutable sur Kubernetes
- Vérifications post-déploiement

**Sécurité**:
- Analyse statique du code
- Scan de vulnérabilités d'images
- Gestion sécurisée des secrets
- Tests de sécurité automatisés

### 4. Monitoring et Observabilité

**Prometheus**:
- Collecte de métriques application et système
- Stockage temporel des données
- Configuration d'alertes

**Grafana**:
- Dashboards pour visualiser les performances
- Vue d'ensemble du système
- Dashboards spécifiques aux composants

**ELK Stack**:
- Centralisation des logs (Filebeat)
- Stockage et indexation (Elasticsearch)
- Visualisation et recherche (Kibana)

## Flux de travail DevOps

### 1. Développement

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  CODING  │───►│   TEST   │───►│  COMMIT  │───►│   PUSH   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

Les développeurs travaillent sur leur environnement local avec Docker Compose. Ils peuvent exécuter des tests localement avant de pousser vers le dépôt Git.

### 2. Intégration

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│   PULL   │───►│  TESTS   │───►│  BUILD   │───►│  PUBLISH │
│  REQUEST │    │UNITAIRES │    │  IMAGES  │    │  IMAGES  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

Chaque Pull Request déclenche une pipeline CI qui exécute les tests et construit les images Docker.

### 3. Déploiement

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  MERGE   │───►│ DEPLOY TO│───►│ VALIDATE │───►│  DEPLOY  │
│   TO     │    │  STAGING │    │ STAGING  │    │    TO    │
│  MAIN    │    │          │    │          │    │   PROD   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

Le merge sur la branche principale déclenche le déploiement automatique sur l'environnement de staging, puis sur la production après validation.

### 4. Exploitation

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│ MONITOR  │───►│  ALERT   │───►│ RESPOND  │
│          │    │          │    │          │
└──────────┘    └──────────┘    └──────────┘
```

L'application en production est surveillée en permanence. Les alertes sont déclenchées en cas de problème et l'équipe peut réagir rapidement.

## Considérations de mise à l'échelle

Notre architecture est conçue pour évoluer horizontalement à mesure que la charge augmente:

1. **Scaling applicatif**:
   - Les pods d'API peuvent être mis à l'échelle automatiquement en fonction de la charge CPU/mémoire
   - Les services LLM peuvent être mis à l'échelle pour gérer plus d'inférences parallèles

2. **Scaling de base de données**:
   - Possibilité d'ajouter des réplicas en lecture pour les requêtes intensives
   - Sharding possible pour les grands volumes de données

3. **Scaling d'infrastructure**:
   - Ajout de nœuds Kubernetes pour augmenter la capacité du cluster
   - Configuration de quotas de ressources pour garantir la qualité de service

## Sécurité et conformité

Notre architecture intègre plusieurs niveaux de sécurité:

1. **Sécurité réseau**:
   - Isolation des services par namespaces
   - Politique de sécurité réseau pour limiter les communications
   - Ingress TLS pour le chiffrement des communications externes

2. **Sécurité des données**:
   - Secrets Kubernetes pour les informations sensibles
   - Chiffrement des données au repos
   - Backups sécurisés et chiffrés

3. **Sécurité du code**:
   - Analyse statique du code dans le pipeline CI
   - Scan des vulnérabilités des dépendances
   - Scan des images Docker avant déploiement

## Récupération après sinistre

Notre stratégie de récupération après sinistre comprend:

1. **Backups réguliers**:
   - Sauvegardes quotidiennes de la base de données
   - Sauvegarde des configurations et des états

2. **Reprise d'activité**:
   - Procédure documentée pour la restauration des services
   - Infrastructure as Code pour recréer l'environnement
   - Tests réguliers de restauration

## Avantages de cette architecture

- **Portabilité**: peut fonctionner sur n'importe quel environnement Kubernetes
- **Evolutivité**: peut gérer des charges croissantes
- **Résilience**: tolérance aux pannes et récupération automatique
- **Observabilité**: visibilité complète sur le système
- **Automatisation**: déploiements sans intervention manuelle
- **Sécurité**: multiples couches de sécurité intégrées 