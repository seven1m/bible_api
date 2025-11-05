output "storage_account_name" {
  description = "Name of the storage account"
  value       = azurerm_storage_account.bible_storage.name
}

output "storage_account_id" {
  description = "ID of the storage account"
  value       = azurerm_storage_account.bible_storage.id
}

output "primary_connection_string" {
  description = "Primary connection string for the storage account"
  value       = azurerm_storage_account.bible_storage.primary_connection_string
  sensitive   = true
}

output "primary_blob_endpoint" {
  description = "Primary blob endpoint"
  value       = azurerm_storage_account.bible_storage.primary_blob_endpoint
}

output "container_name" {
  description = "Name of the blob container"
  value       = azurerm_storage_container.bible_translations.name
}
