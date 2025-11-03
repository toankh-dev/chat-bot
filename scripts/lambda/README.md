# Lambda Build and Deploy Scripts

Unified scripts for building and deploying Lambda functions and layers for the KASS Chatbot.

## Overview

- **build-all.ps1**: Build Lambda functions and layers
- **deploy.py**: Deploy layers and update function code to AWS

## Prerequisites

- Python 3.11+
- PowerShell (Windows) or PowerShell Core (cross-platform)
- AWS CLI configured with credentials
- pip (Python package installer)

## Quick Start

### 1. Build Everything

```powershell
# Build all functions and layers
powershell .\scripts\lambda\build-all.ps1

# Build only functions (skip layers)
powershell .\scripts\lambda\build-all.ps1 -SkipLayers

# Build only layers (skip functions)
powershell .\scripts\lambda\build-all.ps1 -SkipFunctions

# Clean and rebuild
powershell .\scripts\lambda\build-all.ps1 -Clean
```

### 2. Deploy Infrastructure with Terraform

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### 3. Update Lambda Code (Optional)

After infrastructure is deployed, you can update Lambda function code:

```bash
# Set environment variables
export AWS_REGION=us-east-1
export NAME_PREFIX=kass-chatbot-dev

# Deploy/update Lambda code
python scripts/lambda/deploy.py
```

## Build Script Details

### build-all.ps1

**Purpose**: Build Lambda deployment packages and layers.

**Output Location**: `terraform/dist/`
- Functions: `terraform/dist/functions/*.zip`
- Layers: `terraform/dist/layers/*.zip`

**Parameters**:
- `-SkipLayers`: Skip building Lambda layers
- `-SkipFunctions`: Skip building Lambda functions
- `-Clean`: Clean dist directory before building

**What it builds**:

#### Functions (7 total)
1. **orchestrator**: Main chat orchestrator with LangChain agent
2. **vector_search**: Vector similarity search in OpenSearch
3. **document_processor**: Process and index documents from S3
4. **report_tool**: Generate reports from data
5. **summarize_tool**: Summarize content
6. **code_review_tool**: Review code snippets
7. **discord_handler**: Handle Discord webhook events

#### Layers (3 total)
1. **common-utilities**: boto3, opensearch-py, requests, common utilities
2. **langchain**: LangChain framework and dependencies
3. **document-processing**: pypdf, python-docx, openpyxl

### deploy.py

**Purpose**: Deploy Lambda layers and update function code to AWS.

**Requirements**: Infrastructure must be deployed with Terraform first.

**Environment Variables**:
- `AWS_REGION`: AWS region (default: us-east-1)
- `NAME_PREFIX`: Resource name prefix (default: kass-chatbot-dev)

**What it does**:
1. Deploys Lambda layers (creates new versions)
2. Updates Lambda function code (updates existing functions)

**Note**: This script does NOT create Lambda functions. Use Terraform for initial infrastructure setup.

## Directory Structure

```
kass/
├── scripts/
│   └── lambda/
│       ├── build-all.ps1      # Build script
│       ├── deploy.py          # Deploy script
│       └── README.md          # This file
├── lambda_functions/
│   ├── common/                # Shared utilities
│   ├── orchestrator/          # Orchestrator function
│   ├── vector_search/         # Vector search function
│   ├── document_processor/    # Document processor function
│   └── tools/                 # Tool functions
└── terraform/
    ├── dist/                  # Built packages (gitignored)
    │   ├── functions/         # Function ZIPs
    │   └── layers/            # Layer ZIPs
    └── modules/
        └── lambda/            # Lambda Terraform module
```

## Workflow

### Initial Deployment

```bash
# 1. Build Lambda packages
powershell .\scripts\lambda\build-all.ps1

# 2. Deploy infrastructure with Terraform
cd terraform
terraform init
terraform plan
terraform apply
```

### Update Function Code

After making changes to Lambda function code:

```bash
# 1. Rebuild functions
powershell .\scripts\lambda\build-all.ps1 -SkipLayers

# 2. Update functions in AWS
python scripts/lambda/deploy.py
```

### Update Layers

After updating dependencies:

```bash
# 1. Rebuild layers
powershell .\scripts\lambda\build-all.ps1 -SkipFunctions

# 2. Deploy new layer versions
python scripts/lambda/deploy.py

# 3. Update Terraform to use new layer versions (if needed)
cd terraform
terraform plan
terraform apply
```

## Troubleshooting

### Build fails with "module not found"

Make sure you have Python 3.11+ and pip installed:
```bash
python --version
pip --version
```

### Deploy fails with "Function not found"

The infrastructure must be deployed with Terraform first:
```bash
cd terraform
terraform apply
```

### Layer size too large

Lambda layers have a 250MB (unzipped) limit. If a layer exceeds this:
1. Review dependencies and remove unnecessary packages
2. Use slim/minimal versions of libraries
3. Split into multiple smaller layers

### Permission denied errors

Ensure AWS credentials are configured:
```bash
aws configure
aws sts get-caller-identity
```

## Development Notes

- Lambda functions should use layers for dependencies
- Common utilities should be in the `lambda_functions/common/` directory
- Keep function code minimal - use layers for dependencies
- Test locally before deploying to AWS
- Use Terraform for infrastructure changes, not the deploy script

## See Also

- [Terraform Lambda Module](../../terraform/modules/lambda/)
- [Lambda Functions Source](../../lambda_functions/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
