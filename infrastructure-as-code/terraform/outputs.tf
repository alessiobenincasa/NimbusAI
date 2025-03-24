output "kubernetes_cluster_context" {
  description = "The Kubernetes cluster context used"
  value       = var.kubernetes_context
}

output "app_namespace" {
  description = "The Kubernetes namespace for application"
  value       = kubernetes_namespace.app.metadata[0].name
}

output "monitoring_namespace" {
  description = "The Kubernetes namespace for monitoring"
  value       = kubernetes_namespace.monitoring.metadata[0].name
}

output "gitlab_namespace" {
  description = "The Kubernetes namespace for GitLab"
  value       = kubernetes_namespace.gitlab.metadata[0].name
}

output "database_secret_name" {
  description = "The name of the database credentials secret"
  value       = kubernetes_secret.database_credentials.metadata[0].name
} 