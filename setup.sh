#!/bin/bash

set -e

echo "🚀 Installation de la plateforme DevOps LLM Chatbot"
echo "=================================================="

# Vérification des prérequis
echo "✅ Vérification des prérequis..."

check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ $1 est requis mais non installé."
        echo "   Installation recommandée: $2"
        exit 1
    fi
    echo "✓ $1 est installé"
}

check_command docker "https://docs.docker.com/get-docker/"
check_command kubectl "https://kubernetes.io/docs/tasks/tools/"
check_command k3d "curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash"
check_command terraform "https://learn.hashicorp.com/tutorials/terraform/install-cli"
check_command ansible "pip install ansible"
check_command python3 "https://www.python.org/downloads/"
check_command git "https://git-scm.com/downloads"

# Création du cluster Kubernetes local
echo "🌐 Création du cluster Kubernetes local..."
k3d cluster create llm-chatbot-cluster \
    --api-port 6550 \
    --port 80:80@loadbalancer \
    --port 443:443@loadbalancer \
    --agents 2

# Attente que le cluster soit prêt
echo "⏳ Attente de la disponibilité du cluster..."
kubectl wait --for=condition=Ready nodes --all --timeout=60s

# Installation des outils
echo "🔧 Installation des dépendances Python..."
pip install -r app/requirements.txt

# Création des namespaces Kubernetes
echo "🧩 Configuration des namespaces Kubernetes..."
kubectl create namespace monitoring
kubectl create namespace app
kubectl create namespace gitlab

# Déploiement de l'infrastructure de base
echo "🏗️ Déploiement de l'infrastructure de base..."
kubectl apply -f k8s/namespaces.yaml
kubectl apply -f k8s/storage-class.yaml

# Déploiement de la stack de monitoring
echo "📊 Déploiement de la stack de monitoring..."
kubectl apply -f monitoring/prometheus/
kubectl apply -f monitoring/grafana/
kubectl apply -f monitoring/elk/

# Déploiement de GitLab pour CI/CD
echo "🔄 Déploiement de GitLab CI..."
kubectl apply -f ci-cd/gitlab/

# Installation du registre de conteneurs local
echo "📦 Configuration du registre de conteneurs local..."
docker run -d -p 5000:5000 --restart=always --name registry registry:2

echo "✅ Installation terminée!"
echo ""
echo "Pour accéder aux différents services:"
echo "- API: http://localhost/api"
echo "- Grafana: http://localhost/grafana (admin/admin)"
echo "- Prometheus: http://localhost/prometheus"
echo "- Kibana: http://localhost/kibana"
echo "- GitLab: http://localhost/gitlab (root/password)"
echo ""
echo "Pour commencer à développer: make dev"
echo "Pour déployer l'application: make deploy"
echo "Pour exécuter les tests: make test" 