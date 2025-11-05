resource "azurerm_mssql_server" "bible_sql" {
  name                         = var.sql_server_name
  resource_group_name          = var.resource_group_name
  location                     = var.location
  version                      = "12.0"
  administrator_login          = var.admin_login
  administrator_login_password = var.admin_password
  minimum_tls_version          = "1.2"

  tags = var.tags
}

resource "azurerm_mssql_database" "bible_db" {
  name           = var.sql_database_name
  server_id      = azurerm_mssql_server.bible_sql.id
  collation      = "SQL_Latin1_General_CP1_CI_AS"
  max_size_gb    = 2
  sku_name       = "Basic"
  zone_redundant = false

  tags = var.tags
}

# Firewall rule to allow Azure services
resource "azurerm_mssql_firewall_rule" "allow_azure_services" {
  name             = "AllowAzureServices"
  server_id        = azurerm_mssql_server.bible_sql.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

# Optional: Firewall rule for your IP (update with your IP)
resource "azurerm_mssql_firewall_rule" "allow_client_ip" {
  count            = var.client_ip_address != null ? 1 : 0
  name             = "AllowClientIP"
  server_id        = azurerm_mssql_server.bible_sql.id
  start_ip_address = var.client_ip_address
  end_ip_address   = var.client_ip_address
}
