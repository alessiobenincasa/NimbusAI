.PHONY: setup dev build deploy test clean logs monitoring infra

# Configuration
APP_NAME = llm-chatbot
VERSION ?= $(shell git describe --tags --always --dirty)
REGISTRY = localhost:5000
NAMESPACE = app
K8S_CONTEXT = k3d-llm-chatbot-cluster

# Commandes principales
setup:
	@chmod +x setup.sh
	@./setup.sh

dev:
	@echo "🚀 Démarrage de l'environnement de développement..."
	docker-compose up -d

build:
	@echo "🔨 Construction des images Docker..."
	docker build -t $(REGISTRY)/$(APP_NAME)-api:$(VERSION) ./app/api
	docker build -t $(REGISTRY)/$(APP_NAME)-llm:$(VERSION) ./app/llm
	docker build -t $(REGISTRY)/$(APP_NAME)-database:$(VERSION) ./app/database
	docker push $(REGISTRY)/$(APP_NAME)-api:$(VERSION)
	docker push $(REGISTRY)/$(APP_NAME)-llm:$(VERSION)
	docker push $(REGISTRY)/$(APP_NAME)-database:$(VERSION)

deploy: build
	@echo "📦 Déploiement sur Kubernetes..."
	cd k8s && VERSION=$(VERSION) envsubst < api/deployment.yaml | kubectl apply -f -
	cd k8s && VERSION=$(VERSION) envsubst < llm/deployment.yaml | kubectl apply -f -
	cd k8s && VERSION=$(VERSION) envsubst < database/deployment.yaml | kubectl apply -f -
	kubectl apply -f k8s/ingress.yaml
	@echo "✅ Déploiement terminé!"

test:
	@echo "🧪 Exécution des tests..."
	source .venv/bin/activate && cd app && pytest

clean:
	@echo "🧹 Nettoyage complet de l'environnement..."
	@echo "🔽 Arrêt des conteneurs Docker..."
	docker-compose down || true
	
	@echo "🗑️ Suppression des namespaces Kubernetes..."
	kubectl delete namespace $(NAMESPACE) || true
	kubectl delete namespace monitoring || true
	kubectl delete namespace gitlab || true
	
	@echo "🗑️ Suppression du registre Docker..."
	docker stop registry || true
	docker rm registry || true
	
	@echo "🗑️ Suppression du cluster K3d..."
	k3d cluster delete llm-chatbot-cluster || true
	
	@echo "🗑️ Suppression de l'environnement virtuel Python..."
	rm -rf .venv || true
	
	@echo "🗑️ Nettoyage des caches Python..."
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "*.pyd" -delete
	find . -name ".pytest_cache" -type d -exec rm -rf {} +
	find . -name ".coverage" -delete
	find . -name "htmlcov" -type d -exec rm -rf {} +
	
	@echo "✅ Nettoyage terminé! L'environnement a été complètement réinitialisé."

logs:
	@echo "📋 Affichage des logs..."
	kubectl logs -f -l app=$(APP_NAME) -n $(NAMESPACE)

monitoring:
	@echo "📊 Accès au dashboard de monitoring..."
	xdg-open http://localhost/grafana || open http://localhost/grafana

infra:
	@echo "🏗️ Déploiement de l'infrastructure avec Terraform..."
	cd infrastructure-as-code/terraform && terraform init && terraform apply -auto-approve

# Commandes avancées
scale:
	@echo "⚖️ Mise à l'échelle des pods..."
	kubectl scale deployment $(APP_NAME)-api -n $(NAMESPACE) --replicas=$(REPLICAS)

rollback:
	@echo "⏮️ Rollback à la version précédente..."
	kubectl rollout undo deployment/$(APP_NAME)-api -n $(NAMESPACE)
	kubectl rollout undo deployment/$(APP_NAME)-llm -n $(NAMESPACE)

status:
	@echo "ℹ️ Statut des déploiements:"
	kubectl get pods,svc,ingress -n $(NAMESPACE)
	@echo "\nℹ️ Statut du monitoring:"
	kubectl get pods,svc -n monitoring

help:
	@echo "🔍 Commandes disponibles:"
	@echo "  setup      : Initialise l'environnement complet"
	@echo "  dev        : Démarre l'environnement de développement avec docker-compose"
	@echo "  build      : Construit et pousse les images Docker"
	@echo "  deploy     : Déploie l'application sur Kubernetes"
	@echo "  test       : Exécute les tests"
	@echo "  clean      : Nettoie l'environnement"
	@echo "  logs       : Affiche les logs de l'application"
	@echo "  monitoring : Ouvre le dashboard Grafana"
	@echo "  infra      : Déploie l'infrastructure avec Terraform"
	@echo "  scale      : Ajuste le nombre de réplicas (usage: make scale REPLICAS=3)"
	@echo "  rollback   : Revient à la version précédente"
	@echo "  status     : Affiche le statut des déploiements" 