variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "bibleapi"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "eastus"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "Bible API"
    ManagedBy   = "Terraform"
  }
}

variable "blob_container_name" {
  description = "Name of the blob container for Bible XML files"
  type        = string
  default     = "bible-translations"
}

variable "create_sql_database" {
  description = "Whether to create SQL database resources"
  type        = bool
  default     = false
}

variable "sql_admin_username" {
  description = "SQL Server administrator username"
  type        = string
  default     = "sqladmin"
  sensitive   = true
}

variable "sql_admin_password" {
  description = "SQL Server administrator password"
  type        = string
  sensitive   = true
  default     = null
}

variable "acr_sku" {
  description = "SKU for Azure Container Registry"
  type        = string
  default     = "Basic"

  validation {
    condition     = contains(["Basic", "Standard", "Premium"], var.acr_sku)
    error_message = "ACR SKU must be Basic, Standard, or Premium."
  }
}

variable "docker_image_name" {
  description = "Docker image name and tag"
  type        = string
  default     = "bible-api:latest"
}
