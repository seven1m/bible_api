resource "azurerm_storage_account" "bible_storage" {
  name                     = replace(lower(var.storage_account_name), "-", "")
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"

  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false

  blob_properties {
    cors_rule {
      allowed_origins    = ["*"]
      allowed_methods    = ["GET", "HEAD", "OPTIONS"]
      allowed_headers    = ["*"]
      exposed_headers    = ["*"]
      max_age_in_seconds = 3600
    }

    delete_retention_policy {
      days = 7
    }
  }

  tags = var.tags
}

resource "azurerm_storage_container" "bible_translations" {
  name                  = var.container_name
  storage_account_name  = azurerm_storage_account.bible_storage.name
  container_access_type = "private"
}
