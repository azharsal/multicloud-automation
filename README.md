# Multi-Cloud Infrastructure Automation

A Python automation tool for provisioning and managing virtual machines across multiple cloud providers (Azure and GCP) using a unified configuration format.

## Features

- **Multi-Cloud Support**: Deploy to Azure and Google Cloud Platform from a single tool
- **Configuration-Driven**: Define infrastructure in simple `.conf` files
- **Automated Provisioning**: Create VMs with specified OS, size, and networking
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Tech Stack

- Python 3
- Azure SDK (azure-mgmt-compute, azure-identity)
- Google Cloud SDK (google-cloud-compute)
- ConfigParser

## Configuration Format

```ini
[azure01]
purpose = webserver
os = linux
name = linuxServer01
resource-group = images
image = Ubuntu2204
location = canadacentral
admin-username = azureuser
```

## Usage

```bash
# Deploy all VMs defined in config
python automate.py azure.conf

# Deploy with specific options
python automate.py azure.conf --dry-run
python automate.py gcp.conf --verbose
```

## Project Structure

```
├── automate.py      # Main automation script
├── azure.conf       # Azure VM configurations
├── gcp.conf         # GCP VM configurations
└── readme           # Original assignment instructions
```

## Supported Cloud Features

### Azure
- Resource group management
- VM creation with various images (Ubuntu, Windows Server)
- Network security groups
- Multiple regions (canadacentral, westus3, etc.)

### Google Cloud Platform
- Project and zone selection
- Machine type configuration
- Boot disk and image selection

## What I Learned

- Infrastructure as Code (IaC) principles
- Cloud provider APIs and SDKs
- Multi-cloud architecture patterns
- Authentication and credential management
- Resource lifecycle management
