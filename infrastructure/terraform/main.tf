terraform {
  required_version = ">= 1.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}

# Resource Group
resource "azurerm_resource_group" "bible_api" {
  name     = "${var.project_name}-${var.environment}-rg"
  location = var.location
  tags     = var.tags
}

# Storage Account for Bible XML files
module "blob_storage" {
  source = "./modules/blob-storage"

  resource_group_name = azurerm_resource_group.bible_api.name
  location            = azurerm_resource_group.bible_api.location
  storage_account_name = "${var.project_name}${var.environment}sa"
  container_name      = var.blob_container_name
  tags                = var.tags
}

# SQL Database (Optional - for production data)
module "sql_database" {
  source = "./modules/sql-database"
  count  = var.create_sql_database ? 1 : 0

  resource_group_name   = azurerm_resource_group.bible_api.name
  location              = azurerm_resource_group.bible_api.location
  sql_server_name       = "${var.project_name}-${var.environment}-sqlserver"
  sql_database_name     = "${var.project_name}-${var.environment}-db"
  admin_login           = var.sql_admin_username
  admin_password        = var.sql_admin_password
  tags                  = var.tags
}

# Container Registry for Docker images
resource "azurerm_container_registry" "bible_acr" {
  name                = "${var.project_name}${var.environment}acr"
  resource_group_name = azurerm_resource_group.bible_api.name
  location            = azurerm_resource_group.bible_api.location
  sku                 = var.acr_sku
  admin_enabled       = true
  tags                = var.tags
}

# Application Insights for monitoring
resource "azurerm_application_insights" "bible_api" {
  name                = "${var.project_name}-${var.environment}-insights"
  resource_group_name = azurerm_resource_group.bible_api.name
  location            = azurerm_resource_group.bible_api.location
  application_type    = "web"
  tags                = var.tags
}

# App Service Plan
module "app_service" {
  source = "./modules/app-service"

  resource_group_name         = azurerm_resource_group.bible_api.name
  location                    = azurerm_resource_group.bible_api.location
  app_service_plan_name       = "${var.project_name}-${var.environment}-plan"
  app_service_name            = "${var.project_name}-${var.environment}-app"
  docker_registry_url         = azurerm_container_registry.bible_acr.login_server
  docker_registry_username    = azurerm_container_registry.bible_acr.admin_username
  docker_registry_password    = azurerm_container_registry.bible_acr.admin_password
  docker_image_name           = var.docker_image_name
  storage_connection_string   = module.blob_storage.primary_connection_string
  blob_container_name         = var.blob_container_name
  app_insights_key            = azurerm_application_insights.bible_api.instrumentation_key
  app_insights_connection     = azurerm_application_insights.bible_api.connection_string
  sql_connection_string       = var.create_sql_database ? module.sql_database[0].connection_string : ""
  tags                        = var.tags
}
