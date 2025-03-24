# Guide des Commandes DevOps

Ce document recense les principales commandes utilisées dans notre plateforme DevOps pour le chatbot LLM.

## Table des matières

1. [Make](#make)
2. [Docker](#docker)
3. [Kubernetes](#kubernetes)
4. [Terraform](#terraform)
5. [Ansible](#ansible)
6. [Git](#git)
7. [CI/CD](#ci-cd)

## Make

Notre Makefile fournit des raccourcis pour les commandes fréquentes:

| Commande | Description |
|----------|-------------|
| `make setup` | Initialise l'environnement complet |
| `make dev` | Démarre l'environnement de développement avec Docker Compose |
| `make build` | Construit et pousse les images Docker |
| `make deploy` | Déploie l'application sur Kubernetes |
| `make test` | Exécute les tests |
| `make clean` | Nettoie l'environnement |
| `make logs` | Affiche les logs de l'application |
| `make monitoring` | Ouvre le dashboard Grafana |
| `make infra` | Déploie l'infrastructure avec Terraform |
| `make scale REPLICAS=3` | Ajuste le nombre de réplicas |
| `make rollback` | Revient à la version précédente |
| `make status` | Affiche le statut des déploiements |

## Docker

### Images

| Commande | Description |
|----------|-------------|
| `docker build -t image:tag .` | Construit une image |
| `docker push registry/image:tag` | Pousse une image vers le registre |
| `docker pull registry/image:tag` | Récupère une image du registre |
| `docker images` | Liste les images locales |

### Conteneurs

| Commande | Description |
|----------|-------------|
| `docker run -p 8000:8000 image:tag` | Lance un conteneur |
| `docker ps` | Liste les conteneurs actifs |
| `docker ps -a` | Liste tous les conteneurs |
| `docker stop container_id` | Arrête un conteneur |
| `docker rm container_id` | Supprime un conteneur |
| `docker logs container_id` | Affiche les logs d'un conteneur |
| `docker exec -it container_id bash` | Exécute un shell dans un conteneur |

### Docker Compose

| Commande | Description |
|----------|-------------|
| `docker-compose up -d` | Démarre tous les services en arrière-plan |
| `docker-compose down` | Arrête et supprime tous les conteneurs |
| `docker-compose logs -f [service]` | Affiche les logs en continu |
| `docker-compose ps` | Liste les services en cours d'exécution |
| `docker-compose restart [service]` | Redémarre un service |

## Kubernetes

### Commandes de base

| Commande | Description |
|----------|-------------|
| `kubectl get pods` | Liste les pods |
| `kubectl get pods -n namespace` | Liste les pods dans un namespace |
| `kubectl get svc` | Liste les services |
| `kubectl get deployments` | Liste les déploiements |
| `kubectl get nodes` | Liste les nœuds du cluster |
| `kubectl get all` | Liste toutes les ressources |

### Déploiement et gestion

| Commande | Description |
|----------|-------------|
| `kubectl apply -f file.yaml` | Applique une configuration |
| `kubectl delete -f file.yaml` | Supprime une configuration |
| `kubectl rollout status deployment/name` | Affiche le statut d'un déploiement |
| `kubectl rollout history deployment/name` | Affiche l'historique d'un déploiement |
| `kubectl rollout undo deployment/name` | Revient à la version précédente |
| `kubectl scale deployment/name --replicas=3` | Modifie le nombre de réplicas |

### Débogage

| Commande | Description |
|----------|-------------|
| `kubectl logs pod_name` | Affiche les logs d'un pod |
| `kubectl logs -f pod_name` | Affiche les logs en continu |
| `kubectl describe pod pod_name` | Affiche les détails d'un pod |
| `kubectl exec -it pod_name -- bash` | Exécute un shell dans un pod |
| `kubectl port-forward pod_name 8000:8000` | Transfère un port local vers un pod |
| `kubectl get events` | Affiche les événements du cluster |

### K3d (Kubernetes local)

| Commande | Description |
|----------|-------------|
| `k3d cluster create name` | Crée un cluster local |
| `k3d cluster list` | Liste les clusters locaux |
| `k3d cluster delete name` | Supprime un cluster local |
| `k3d cluster start name` | Démarre un cluster existant |
| `k3d cluster stop name` | Arrête un cluster existant |

## Terraform

### Commandes de base

| Commande | Description |
|----------|-------------|
| `terraform init` | Initialise un répertoire de travail Terraform |
| `terraform plan` | Crée un plan d'exécution |
| `terraform apply` | Applique les changements |
| `terraform destroy` | Détruit l'infrastructure gérée |
| `terraform validate` | Valide les fichiers de configuration |
| `terraform fmt` | Formate les fichiers de configuration |

### Gestion des états

| Commande | Description |
|----------|-------------|
| `terraform state list` | Liste les ressources dans l'état Terraform |
| `terraform state show resource` | Affiche les détails d'une ressource |
| `terraform state pull` | Exporte l'état actuel |
| `terraform state push file` | Importe un état spécifique |

## Ansible

### Commandes de base

| Commande | Description |
|----------|-------------|
| `ansible-playbook playbook.yml` | Exécute un playbook |
| `ansible-playbook -i inventory playbook.yml` | Avec un inventaire spécifique |
| `ansible-playbook playbook.yml --check` | Mode simulation |
| `ansible-playbook playbook.yml --diff` | Montre les différences |
| `ansible-playbook playbook.yml --tags "tag1,tag2"` | Exécute des tâches spécifiques |

## Git

### Commandes de base

| Commande | Description |
|----------|-------------|
| `git clone url` | Clone un dépôt |
| `git pull` | Récupère les derniers changements |
| `git push` | Pousse les changements locaux |
| `git add file` | Ajoute un fichier à l'index |
| `git commit -m "message"` | Crée un commit |
| `git checkout -b branch_name` | Crée et bascule sur une nouvelle branche |
| `git merge branch_name` | Fusionne une branche dans la branche courante |

## CI/CD

### GitLab CI

| Commande | Description |
|----------|-------------|
| `gitlab-runner register` | Enregistre un runner GitLab |
| `gitlab-runner list` | Liste les runners |
| `gitlab-runner start` | Démarre le service runner |
| `gitlab-runner stop` | Arrête le service runner |
| `gitlab-runner run` | Démarre un runner en mode foreground |

### Variables d'environnement courantes

| Variable | Description |
|----------|-------------|
| `CI_COMMIT_SHA` | Hash du commit |
| `CI_COMMIT_REF_NAME` | Nom de la branche ou du tag |
| `CI_PIPELINE_ID` | ID du pipeline |
| `CI_PROJECT_DIR` | Chemin du projet |
| `CI_REGISTRY` | URL du registre d'images | 