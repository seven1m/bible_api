variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "sql_server_name" {
  description = "Name of the SQL Server"
  type        = string
}

variable "sql_database_name" {
  description = "Name of the SQL Database"
  type        = string
}

variable "admin_login" {
  description = "Administrator login for SQL Server"
  type        = string
  sensitive   = true
}

variable "admin_password" {
  description = "Administrator password for SQL Server"
  type        = string
  sensitive   = true
}

variable "client_ip_address" {
  description = "Client IP address to allow through firewall (optional)"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
