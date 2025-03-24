terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.10"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.5"
    }
  }
}

provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = var.kubernetes_context
}

provider "helm" {
  kubernetes {
    config_path    = "~/.kube/config"
    config_context = var.kubernetes_context
  }
}

# Namespaces
resource "kubernetes_namespace" "app" {
  metadata {
    name = "app"
    labels = {
      name        = "app"
      environment = var.environment
    }
  }
}

resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = "monitoring"
    labels = {
      name        = "monitoring"
      environment = var.environment
    }
  }
}

resource "kubernetes_namespace" "gitlab" {
  metadata {
    name = "gitlab"
    labels = {
      name        = "gitlab"
      environment = var.environment
    }
  }
}

# Storage Class
resource "kubernetes_storage_class" "local_storage" {
  metadata {
    name = "local-storage"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "true"
    }
  }
  storage_provisioner = "k8s.io/minikube-hostpath"
  reclaim_policy      = "Delete"
  volume_binding_mode = "Immediate"
}

# Database Credentials
resource "kubernetes_secret" "database_credentials" {
  metadata {
    name      = "database-credentials"
    namespace = kubernetes_namespace.app.metadata[0].name
  }

  data = {
    username = "postgres"
    password = var.db_password
    url      = "postgresql://postgres:${var.db_password}@llm-chatbot-database:5432/llmchatbot"
  }

  type = "Opaque"
}

# Monitoring
module "prometheus" {
  source = "./modules/prometheus"
  namespace = kubernetes_namespace.monitoring.metadata[0].name
  depends_on = [kubernetes_namespace.monitoring]
}

module "grafana" {
  source = "./modules/grafana"
  namespace = kubernetes_namespace.monitoring.metadata[0].name
  depends_on = [kubernetes_namespace.monitoring, module.prometheus]
}

module "elk" {
  source = "./modules/elk"
  namespace = kubernetes_namespace.monitoring.metadata[0].name
  depends_on = [kubernetes_namespace.monitoring]
}

# CI/CD
module "gitlab" {
  source = "./modules/gitlab"
  namespace = kubernetes_namespace.gitlab.metadata[0].name
  depends_on = [kubernetes_namespace.gitlab]
} 