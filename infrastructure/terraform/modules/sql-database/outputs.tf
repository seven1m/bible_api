output "sql_server_id" {
  description = "ID of the SQL Server"
  value       = azurerm_mssql_server.bible_sql.id
}

output "sql_server_fqdn" {
  description = "Fully qualified domain name of the SQL Server"
  value       = azurerm_mssql_server.bible_sql.fully_qualified_domain_name
}

output "sql_database_id" {
  description = "ID of the SQL Database"
  value       = azurerm_mssql_database.bible_db.id
}

output "sql_database_name" {
  description = "Name of the SQL Database"
  value       = azurerm_mssql_database.bible_db.name
}

output "connection_string" {
  description = "Connection string for the SQL Database"
  value       = "Server=tcp:${azurerm_mssql_server.bible_sql.fully_qualified_domain_name},1433;Initial Catalog=${azurerm_mssql_database.bible_db.name};Persist Security Info=False;User ID=${var.admin_login};Password=${var.admin_password};MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;"
  sensitive   = true
}
