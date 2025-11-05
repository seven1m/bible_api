output "app_service_id" {
  description = "ID of the App Service"
  value       = azurerm_linux_web_app.bible_api.id
}

output "app_service_name" {
  description = "Name of the App Service"
  value       = azurerm_linux_web_app.bible_api.name
}

output "app_service_url" {
  description = "Default hostname of the App Service"
  value       = "https://${azurerm_linux_web_app.bible_api.default_hostname}"
}

output "app_service_plan_id" {
  description = "ID of the App Service Plan"
  value       = azurerm_service_plan.bible_api.id
}

output "app_service_principal_id" {
  description = "Principal ID of the App Service managed identity"
  value       = azurerm_linux_web_app.bible_api.identity[0].principal_id
}
