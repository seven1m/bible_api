variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "app_service_plan_name" {
  description = "Name of the App Service Plan"
  type        = string
}

variable "app_service_name" {
  description = "Name of the App Service"
  type        = string
}

variable "sku_name" {
  description = "SKU name for the App Service Plan"
  type        = string
  default     = "B1"
}

variable "docker_registry_url" {
  description = "Docker registry URL"
  type        = string
}

variable "docker_registry_username" {
  description = "Docker registry username"
  type        = string
  sensitive   = true
}

variable "docker_registry_password" {
  description = "Docker registry password"
  type        = string
  sensitive   = true
}

variable "docker_image_name" {
  description = "Docker image name with tag"
  type        = string
}

variable "storage_connection_string" {
  description = "Storage account connection string"
  type        = string
  sensitive   = true
}

variable "blob_container_name" {
  description = "Name of the blob container"
  type        = string
}

variable "app_insights_key" {
  description = "Application Insights instrumentation key"
  type        = string
  sensitive   = true
}

variable "app_insights_connection" {
  description = "Application Insights connection string"
  type        = string
  sensitive   = true
}

variable "sql_connection_string" {
  description = "SQL Database connection string"
  type        = string
  sensitive   = true
  default     = ""
}

variable "cors_allowed_origins" {
  description = "CORS allowed origins"
  type        = list(string)
  default     = ["*"]
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
