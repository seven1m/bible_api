output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.bible_api.name
}

output "storage_account_name" {
  description = "Name of the storage account"
  value       = module.blob_storage.storage_account_name
}

output "storage_connection_string" {
  description = "Connection string for the storage account"
  value       = module.blob_storage.primary_connection_string
  sensitive   = true
}

output "container_registry_name" {
  description = "Name of the container registry"
  value       = azurerm_container_registry.bible_acr.name
}

output "container_registry_login_server" {
  description = "Login server for the container registry"
  value       = azurerm_container_registry.bible_acr.login_server
}

output "container_registry_admin_username" {
  description = "Admin username for container registry"
  value       = azurerm_container_registry.bible_acr.admin_username
  sensitive   = true
}

output "container_registry_admin_password" {
  description = "Admin password for container registry"
  value       = azurerm_container_registry.bible_acr.admin_password
  sensitive   = true
}

output "app_service_url" {
  description = "URL of the App Service"
  value       = module.app_service.app_service_url
}

output "app_service_name" {
  description = "Name of the App Service"
  value       = module.app_service.app_service_name
}

output "application_insights_key" {
  description = "Application Insights instrumentation key"
  value       = azurerm_application_insights.bible_api.instrumentation_key
  sensitive   = true
}

output "application_insights_connection_string" {
  description = "Application Insights connection string"
  value       = azurerm_application_insights.bible_api.connection_string
  sensitive   = true
}

output "sql_server_fqdn" {
  description = "Fully qualified domain name of the SQL server"
  value       = var.create_sql_database ? module.sql_database[0].sql_server_fqdn : null
}

output "sql_database_name" {
  description = "Name of the SQL database"
  value       = var.create_sql_database ? module.sql_database[0].sql_database_name : null
}
