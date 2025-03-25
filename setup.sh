#!/bin/bash

set -e

echo "🚀 Installation de la plateforme DevOps LLM Chatbot"
echo "=================================================="

# Fonction pour vérifier et installer les dépendances système
install_system_dependency() {
    local package=$1
    local install_command=$2
    local package_manager=$3

    if ! command -v $package &> /dev/null; then
        echo "📦 $package est requis mais non installé. Tentative d'installation..."
        
        if [[ "$OSTYPE" == "darwin"* ]] && [[ "$package_manager" == "brew" ]]; then
            if ! command -v brew &> /dev/null; then
                echo "❌ Homebrew n'est pas installé. Installation recommandée: https://brew.sh/"
                echo "   Ou installez $package manuellement: $install_command"
                return 1
            fi
            brew install $package
        elif [[ "$OSTYPE" == "linux-gnu"* ]] && [[ "$package_manager" == "apt" ]]; then
            if ! command -v apt-get &> /dev/null; then
                echo "❌ apt-get n'est pas disponible. Installez $package manuellement: $install_command"
                return 1
            fi
            sudo apt-get update && sudo apt-get install -y $package
        else
            echo "❌ Installation automatique non prise en charge pour votre système."
            echo "   Installez $package manuellement: $install_command"
            return 1
        fi
        
        echo "✅ $package installé avec succès"
    else
        echo "✓ $package est déjà installé"
    fi
    
    return 0
}

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

# Installation des dépendances système pour la compilation
echo "🔧 Vérification des dépendances système pour la compilation..."
install_system_dependency bc "bc" "brew"
install_system_dependency cmake "cmake" "brew"
install_system_dependency pkg-config "pkg-config" "brew"
install_system_dependency make "make" "brew"

# Création du cluster Kubernetes local
echo "🌐 Création du cluster Kubernetes local..."
k3d cluster create llm-chatbot-cluster \
    --api-port 6550 \
    --port 80:80@loadbalancer \
    --port 443:443@loadbalancer \
    --agents 2 || echo "⚠️ Le cluster existe peut-être déjà, on continue..."

# Attente que le cluster soit prêt
echo "⏳ Attente de la disponibilité du cluster..."
kubectl wait --for=condition=Ready nodes --all --timeout=60s || echo "⚠️ Timeout ou erreur en attendant les nœuds, on continue..."

# Installation des outils
echo "🔧 Installation des dépendances Python..."
echo "🔧 Création d'un environnement virtuel Python..."
python3 -m venv .venv
source .venv/bin/activate
echo "✅ Environnement virtuel activé"

# Mettre à jour pip vers la dernière version
echo "🔄 Mise à jour de pip et setuptools..."
python3 -m pip install --upgrade pip setuptools wheel

# Vérification de la version de Python
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "🔍 Version Python détectée: $PYTHON_VERSION"

# Installation directe des dépendances
echo "🔧 Installation des dépendances Python... (Peut prendre plusieurs minutes)"
python3 -m pip install -r app/api/requirements.txt
python3 -m pip install -r app/llm/requirements.txt

# En cas d'erreur, logique de secours
if [ $? -ne 0 ]; then
    echo "⚠️ Des erreurs se sont produites lors de l'installation des dépendances, tentative de résolution..."
    
    # Installation des dépendances non-problématiques
    echo "🔧 Installation des dépendances non-problématiques..."
    grep -v -E "tokenizers|torch|torchvision|sentencepiece|psycopg" app/api/requirements.txt > app/api/requirements.tmp.txt
    grep -v -E "tokenizers|torch|torchvision|sentencepiece|psycopg" app/llm/requirements.txt > app/llm/requirements.tmp.txt
    
    python3 -m pip install -r app/api/requirements.tmp.txt || echo "⚠️ Erreur lors de l'installation de certaines dépendances API"
    python3 -m pip install -r app/llm/requirements.tmp.txt || echo "⚠️ Erreur lors de l'installation de certaines dépendances LLM"
    
    # Installation des packages problématiques
    echo "🔧 Installation des packages problématiques..."
    
    # Torch et torchvision
    echo "📦 Installation de torch et torchvision..."
    python3 -m pip install torch>=2.3.1 torchvision>=0.21.0 || echo "⚠️ Erreur lors de l'installation de torch/torchvision"
    
    # Pilote PostgreSQL
    echo "📦 Installation d'un pilote PostgreSQL..."
    python3 -m pip install psycopg || python3 -m pip install psycopg2-binary || echo "⚠️ Erreur lors de l'installation du pilote PostgreSQL"
    
    # Packages de traitement de texte
    echo "📦 Installation des packages de traitement de texte..."
    python3 -m pip install tokenizers --only-binary=:all: || echo "⚠️ Erreur lors de l'installation de tokenizers"
    python3 -m pip install sentencepiece --only-binary=:all: || echo "⚠️ Erreur lors de l'installation de sentencepiece"
    
    # Nettoyer
    rm -f app/api/requirements.tmp.txt
    rm -f app/llm/requirements.tmp.txt
fi

# Création des namespaces Kubernetes
echo "🧩 Configuration des namespaces Kubernetes..."
kubectl create namespace monitoring || echo "Le namespace monitoring existe déjà"
kubectl create namespace app || echo "Le namespace app existe déjà"
kubectl create namespace gitlab || echo "Le namespace gitlab existe déjà"

# Déploiement de l'infrastructure de base
echo "🏗️ Déploiement de l'infrastructure de base..."
kubectl apply -f k8s/namespaces.yaml || echo "⚠️ Erreur lors de l'application de k8s/namespaces.yaml"
kubectl apply -f k8s/storage-class.yaml || echo "⚠️ Erreur lors de l'application de k8s/storage-class.yaml"

# Déploiement de la stack de monitoring
echo "📊 Déploiement de la stack de monitoring..."

# Prometheus - essayer d'abord la version correcte des manifestes
if [ -f monitoring/prometheus/prometheus-configmap.yaml ]; then
  kubectl apply -f monitoring/prometheus/prometheus-configmap.yaml
else
  kubectl apply -f monitoring/prometheus/ --validate=false || echo "⚠️ Erreur lors de l'application des fichiers de monitoring/prometheus/"
fi

kubectl apply -f monitoring/grafana/ || echo "⚠️ Erreur lors de l'application des fichiers de monitoring/grafana/"

# ELK - essayer d'abord la version correcte des manifestes
if [ -f monitoring/elk/filebeat-configmap.yaml ]; then
  kubectl apply -f monitoring/elk/filebeat-configmap.yaml
else
  kubectl apply -f monitoring/elk/ --validate=false || echo "⚠️ Erreur lors de l'application des fichiers de monitoring/elk/"
fi

# Déploiement de GitLab pour CI/CD
echo "🔄 Déploiement de GitLab CI..."
kubectl apply -f ci-cd/gitlab/ || echo "⚠️ Erreur lors de l'application des fichiers de ci-cd/gitlab/"

# Installation du registre de conteneurs local
echo "📦 Configuration du registre de conteneurs local..."
docker run -d -p 5000:5000 --restart=always --name registry registry:2 || echo "Le registre de conteneurs est déjà en cours d'exécution"

# Création des répertoires nécessaires s'ils n'existent pas
echo "🔧 Vérification des répertoires de configuration..."
mkdir -p monitoring/prometheus
mkdir -p monitoring/grafana
mkdir -p monitoring/elk
mkdir -p ci-cd/gitlab

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

echo "👉 Pour activer l'environnement virtuel dans le futur, exécutez:"
echo "source .venv/bin/activate" 