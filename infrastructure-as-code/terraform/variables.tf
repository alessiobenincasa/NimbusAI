variable "kubernetes_context" {
  description = "The Kubernetes context to use"
  type        = string
  default     = "k3d-llm-chatbot-cluster"
}

variable "environment" {
  description = "Environment (production, staging, development)"
  type        = string
  default     = "production"
}

variable "db_password" {
  description = "Password for the database"
  type        = string
  default     = "postgres"
  sensitive   = true
}

variable "app_replicas" {
  description = "Number of API replicas"
  type        = number
  default     = 3
}

variable "llm_replicas" {
  description = "Number of LLM service replicas"
  type        = number
  default     = 2
} 