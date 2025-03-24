# LLM Chatbot DevOps - Documentation

Cette documentation décrit l'architecture complète de notre plateforme DevOps pour le chatbot LLM.

## Table des matières

1. [Architecture](#architecture)
2. [Installation](#installation)
3. [Développement](#développement)
4. [Déploiement](#déploiement)
5. [Monitoring](#monitoring)
6. [CI/CD](#ci-cd)
7. [Infrastructure as Code](#infrastructure-as-code)
8. [Maintenance](#maintenance)

## Architecture

Notre plateforme est composée des éléments suivants:

![Architecture](./images/architecture.png)

### Composants principaux

- **API** - API REST développée avec FastAPI
- **LLM Service** - Service d'inférence LLM utilisant LangChain et Hugging Face
- **Base de données** - PostgreSQL pour le stockage des données
- **Kubernetes** - Orchestration des conteneurs
- **Prometheus/Grafana** - Monitoring et alerting
- **ELK Stack** - Gestion centralisée des logs
- **GitLab CI** - Intégration et déploiement continu

## Installation

### Prérequis

- Docker
- Kubernetes (K3d pour le développement local)
- Kubectl
- Python 3.9+
- Terraform (optionnel, pour l'infrastructure as code)
- Ansible (optionnel, pour la configuration)

### Procédure d'installation

1. Cloner le dépôt:

```bash
git clone https://github.com/username/llm-chatbot-devops.git
cd llm-chatbot-devops
```

2. Exécuter le script d'installation:

```bash
chmod +x setup.sh
./setup.sh
```

Le script va:
- Vérifier les prérequis
- Créer un cluster K3d local
- Configurer les namespaces Kubernetes
- Déployer l'infrastructure de base
- Configurer un registre Docker local

## Développement

### Environnement de développement local

Pour démarrer l'environnement de développement:

```bash
make dev
```

Cette commande utilise Docker Compose pour lancer tous les services nécessaires:
- API (http://localhost:8000)
- LLM Service (http://localhost:8001)
- Base de données PostgreSQL (port 5432)
- Prometheus (http://localhost:9090)
- Grafana (http://localhost:3000)
- ELK Stack (http://localhost:5601 pour Kibana)
- GitLab CE (http://localhost:8080)

### Structure du projet

```
.
├── app/                      # Code de l'application
│   ├── api/                  # API REST FastAPI
│   ├── llm/                  # Service LLM
│   └── database/             # Configuration de la base de données
├── ci-cd/                    # Configuration CI/CD
├── docs/                     # Documentation
├── infrastructure-as-code/   # Terraform et Ansible
│   ├── ansible/              # Playbooks Ansible
│   └── terraform/            # Modules Terraform
├── k8s/                      # Manifestes Kubernetes
├── monitoring/               # Configuration de monitoring
│   ├── prometheus/           # Configuration Prometheus
│   ├── grafana/              # Dashboards Grafana
│   └── elk/                  # Configuration ELK
├── docker-compose.yml        # Composition de services pour le développement
├── Makefile                  # Commandes utilitaires
├── README.md                 # Documentation principale
└── setup.sh                  # Script d'installation
```

## Déploiement

### Déploiement sur Kubernetes

Pour déployer l'application sur Kubernetes:

```bash
make deploy
```

Cette commande:
1. Construit les images Docker
2. Les pousse vers le registre
3. Applique les manifestes Kubernetes

### Scaling

Pour modifier le nombre de réplicas:

```bash
make scale REPLICAS=5
```

### Rollback

En cas de problème avec une version déployée:

```bash
make rollback
```

## Monitoring

### Dashboards Grafana

Accès: http://localhost/grafana (en production) ou http://localhost:3000 (en développement)

- **Dashboard principal** - Vue d'ensemble de l'application
- **Dashboard LLM** - Métriques spécifiques au service d'inférence
- **Dashboard Kubernetes** - État du cluster et des pods

### Alertes

Les alertes sont configurées dans Prometheus et peuvent envoyer des notifications via:
- Email
- Slack
- PagerDuty

### Logs

Tous les logs sont centralisés dans l'ELK Stack:
- Filebeat collecte les logs
- Elasticsearch stocke les logs
- Kibana permet de visualiser et chercher dans les logs

## CI/CD

### Pipeline GitLab CI

Notre pipeline CI/CD comprend les étapes suivantes:

1. **Test** - Exécution des tests unitaires et d'intégration
2. **Build** - Construction des images Docker
3. **Deploy** - Déploiement sur Kubernetes
4. **Monitor** - Vérification post-déploiement

### Configuration

Le pipeline est configuré dans le fichier [.gitlab-ci.yml](../ci-cd/.gitlab-ci.yml).

## Infrastructure as Code

### Terraform

Les modules Terraform permettent de:
- Créer les namespaces Kubernetes
- Déployer la stack de monitoring
- Configurer les secrets et les configurations

### Ansible

Les playbooks Ansible permettent de:
- Configurer le cluster Kubernetes
- Installer les outils nécessaires
- Automatiser les tâches de maintenance

## Maintenance

### Backups

Les backups de la base de données sont programmés quotidiennement et stockés de manière sécurisée.

### Mises à jour

Pour mettre à jour l'application:

```bash
git pull
make build
make deploy
```

### Troubleshooting

Pour voir les logs de l'application:

```bash
make logs
```

Pour vérifier l'état des déploiements:

```bash
make status
``` 