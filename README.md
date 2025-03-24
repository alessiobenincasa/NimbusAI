# LLM Chatbot DevOps Platform

Un projet DevOps complet pour déployer, gérer et maintenir une architecture de chatbot LLM.

## Objectif

Ce projet implémente une plateforme DevOps complète pour un chatbot LLM conversationnel capable de discuter des produits d'une marque. L'architecture est conçue pour être facilement adaptable à différentes marques.

## Architecture

Le projet est organisé en plusieurs composants :

- **Application** : API REST, moteur LLM et base de données
- **Infrastructure as Code** : Configuration Terraform et Ansible
- **CI/CD** : Pipeline d'intégration et déploiement continu
- **Kubernetes** : Manifestes de déploiement et configuration
- **Monitoring** : Stack de surveillance et alerting

## Technologies

- **Conteneurisation** : Docker
- **Orchestration** : Kubernetes (K3s pour le développement local)
- **CI/CD** : GitLab CI (auto-hébergé)
- **IaC** : Terraform et Ansible
- **Monitoring** : Prometheus, Grafana, ELK Stack
- **Base de données** : PostgreSQL
- **Backend** : FastAPI (Python)
- **LLM** : Framework local LangChain avec modèles LLM open-source

## Fonctionnalités DevOps

- Déploiement Zero-Downtime
- Auto-scaling horizontal des pods
- Rollbacks automatisés
- Observabilité complète
- Tests automatisés (unit, integration, e2e)
- Infrastructure reproductible
- Sécurité intégrée

## Pour commencer

```bash
# Cloner le projet
git clone https://github.com/username/llm-chatbot-devops.git

# Exécuter le script d'installation
./setup.sh

# Démarrer l'application en mode développement
make dev
```

## Documentation

La documentation détaillée est disponible dans le dossier [docs](./docs/). 