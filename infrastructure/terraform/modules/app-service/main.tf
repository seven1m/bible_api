resource "azurerm_service_plan" "bible_api" {
  name                = var.app_service_plan_name
  resource_group_name = var.resource_group_name
  location            = var.location
  os_type             = "Linux"
  sku_name            = var.sku_name

  tags = var.tags
}

resource "azurerm_linux_web_app" "bible_api" {
  name                = var.app_service_name
  resource_group_name = var.resource_group_name
  location            = var.location
  service_plan_id     = azurerm_service_plan.bible_api.id

  site_config {
    always_on = var.sku_name != "F1" && var.sku_name != "D1"

    application_stack {
      docker_registry_url      = "https://${var.docker_registry_url}"
      docker_registry_username = var.docker_registry_username
      docker_registry_password = var.docker_registry_password
      docker_image_name        = var.docker_image_name
    }

    health_check_path = "/healthz"

    cors {
      allowed_origins = var.cors_allowed_origins
    }
  }

  app_settings = {
    "DOCKER_REGISTRY_SERVER_URL"                 = "https://${var.docker_registry_url}"
    "DOCKER_REGISTRY_SERVER_USERNAME"            = var.docker_registry_username
    "DOCKER_REGISTRY_SERVER_PASSWORD"            = var.docker_registry_password
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE"        = "false"
    "AppSettings__AzureStorageConnectionString"  = var.storage_connection_string
    "AppSettings__AzureContainerName"            = var.blob_container_name
    "APPLICATIONINSIGHTS_CONNECTION_STRING"      = var.app_insights_connection
    "ApplicationInsightsAgent_EXTENSION_VERSION" = "~3"
  }

  https_only = true

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}
