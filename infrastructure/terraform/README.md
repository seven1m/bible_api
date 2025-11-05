# Bible API - Terraform Infrastructure

This directory contains Terraform configuration for deploying the Bible API to Azure.

## Prerequisites

- [Terraform](https://www.terraform.io/downloads.html) >= 1.0
- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
- Azure subscription

## Quick Start

### 1. Login to Azure

```bash
az login
az account set --subscription "your-subscription-id"
```

### 2. Configure Variables

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

### 3. Initialize Terraform

```bash
terraform init
```

### 4. Plan Deployment

```bash
terraform plan
```

### 5. Apply Configuration

```bash
terraform apply
```

## Architecture

The Terraform configuration creates the following Azure resources:

- **Resource Group**: Container for all resources
- **Storage Account**: Blob storage for Bible XML files
- **Container Registry**: Docker image registry
- **App Service Plan**: Hosting plan for the web app
- **App Service**: Linux web app running the containerized API
- **Application Insights**: Application monitoring and telemetry
- **SQL Server & Database** (Optional): Database for Bible verses

## Module Structure

```
terraform/
├── main.tf                    # Main configuration
├── variables.tf               # Input variables
├── outputs.tf                 # Output values
├── terraform.tfvars.example   # Example variable values
└── modules/
    ├── app-service/           # App Service configuration
    ├── blob-storage/          # Blob Storage configuration
    └── sql-database/          # SQL Database configuration
```

## Configuration Variables

### Required Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `project_name` | Project name for resource naming | `bibleapi` |
| `environment` | Environment (dev/staging/prod) | `dev` |
| `location` | Azure region | `eastus` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `create_sql_database` | Create SQL database | `false` |
| `sql_admin_username` | SQL admin username | `sqladmin` |
| `sql_admin_password` | SQL admin password | - |
| `acr_sku` | Container Registry SKU | `Basic` |
| `docker_image_name` | Docker image name | `bible-api:latest` |

## Outputs

After applying, Terraform will output:

- `app_service_url` - URL of the deployed API
- `storage_account_name` - Storage account name
- `container_registry_login_server` - ACR login server
- `application_insights_key` - AppInsights instrumentation key

## Environments

### Development

```hcl
environment = "dev"
create_sql_database = false
acr_sku = "Basic"
```

### Staging

```hcl
environment = "staging"
create_sql_database = true
acr_sku = "Standard"
```

### Production

```hcl
environment = "prod"
create_sql_database = true
acr_sku = "Premium"
```

## Deployment Workflow

### 1. Build and Push Docker Image

```bash
# Build image
docker build -f docker/Dockerfile -t bible-api:latest .

# Tag for ACR
docker tag bible-api:latest <acr-name>.azurecr.io/bible-api:latest

# Login to ACR
az acr login --name <acr-name>

# Push image
docker push <acr-name>.azurecr.io/bible-api:latest
```

### 2. Update App Service

```bash
# Restart App Service to pull latest image
az webapp restart --name <app-service-name> --resource-group <resource-group-name>
```

## Security Best Practices

1. **Never commit `terraform.tfvars`** - It contains sensitive values
2. **Use Azure Key Vault** for secrets in production
3. **Enable firewall rules** on SQL Server
4. **Use managed identities** where possible
5. **Enable HTTPS only** on App Service
6. **Restrict CORS** to specific origins

## State Management

### Remote State (Recommended for Teams)

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "terraform-state-rg"
    storage_account_name = "tfstatestorage"
    container_name       = "tfstate"
    key                  = "bible-api.terraform.tfstate"
  }
}
```

### Local State

By default, state is stored locally in `terraform.tfstate`. Not recommended for teams.

## Cost Estimation

### Development (~$15-20/month)

- App Service Plan (B1): ~$13/month
- Storage Account: ~$1/month
- Container Registry (Basic): ~$5/month
- Application Insights: Free tier

### Production (~$100-150/month)

- App Service Plan (P1V2): ~$80/month
- Storage Account: ~$5/month
- Container Registry (Standard): ~$20/month
- SQL Database (S1): ~$30/month
- Application Insights: ~$5/month

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

## Troubleshooting

### Issue: Name already exists

Azure resource names must be globally unique. Update `project_name` in `terraform.tfvars`.

### Issue: Quota exceeded

Check your Azure subscription quotas:

```bash
az vm list-usage --location eastus -o table
```

### Issue: Authentication failed

Ensure you're logged in:

```bash
az account show
```

## Support

For issues or questions:
- Review [Azure App Service docs](https://docs.microsoft.com/en-us/azure/app-service/)
- Check [Terraform Azure Provider docs](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
