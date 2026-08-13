# Terraform Infrastructure

## Overview

Terraform is used to provision and manage infrastructure on the Proxmox VE hypervisor.

The current implementation demonstrates Infrastructure as Code (IaC) by managing an Ubuntu Server virtual machine through the `bpg/proxmox` Terraform provider.

The workflow is:

```text
Terraform
   │
   ▼
Proxmox API
   │
   ▼
Proxmox VE
   │
   ├── Ubuntu Cloud Image
   │
   └── VM 101: terraform-test
```

## Terraform Environment

| Component        | Configuration             |
| ---------------- | ------------------------- |
| Terraform        | 1.15+                     |
| Provider         | bpg/proxmox               |
| Hypervisor       | Proxmox VE                |
| Proxmox Node     | proxmox                   |
| VM ID            | 101                       |
| VM Name          | terraform-test            |
| Operating System | Ubuntu Server cloud image |
| CPU              | 2 cores                   |
| Memory           | 2048 MB                   |
| Disk             | 20 GB                     |
| Network          | vmbr0                     |
| IP Configuration | DHCP                      |

## Project Structure

```text
terraform/
├── main.tf
├── vm.tf
├── variables.tf
├── outputs.tf
├── terraform.tfvars
└── .terraform.lock.hcl
```

### `main.tf`

Contains the Terraform version requirement, provider configuration, Proxmox authentication, and Ubuntu cloud-image resource.

### `vm.tf`

Defines the Proxmox virtual machine resource.

### `variables.tf`

Contains configurable infrastructure parameters including:

* Proxmox node
* VM name
* VM ID
* CPU
* Memory
* Disk size
* Network bridge
* VM datastore
* Image datastore
* Ubuntu cloud-image URL
* Ubuntu cloud-image filename

### `outputs.tf`

Provides useful deployment information including:

* VM ID
* VM name
* Proxmox node
* VM MAC address

### `terraform.tfvars`

Contains sensitive runtime values such as API credentials and the VM password.

This file is excluded from Git.

## Infrastructure as Code Workflow

Changes are applied using the standard Terraform workflow:

```bash
terraform fmt
terraform validate
terraform plan
terraform apply
```

### Formatting

```bash
terraform fmt
```

Ensures Terraform configuration follows standard formatting.

### Validation

```bash
terraform validate
```

Checks that the Terraform configuration is syntactically valid and internally consistent.

### Planning

```bash
terraform plan
```

Compares the desired configuration against the current Terraform state and real infrastructure.

The current configuration has been verified with:

```text
No changes. Your infrastructure matches the configuration.
```

### Applying

```bash
terraform apply
```

Applies approved infrastructure changes.

The VM has been successfully created and managed by Terraform.

## Current Deployment

Terraform currently manages:

```text
VM ID:       101
VM Name:     terraform-test
Node:        proxmox
MAC Address: BC:24:11:81:94:CD
```

The VM is configured with:

* 2 CPU cores
* 2048 MB RAM
* 20 GB virtual disk
* DHCP networking
* `vmbr0` network bridge
* Ubuntu Server cloud image

## State Management

Terraform state is stored locally in the Terraform project directory.

State files are excluded from Git using the repository `.gitignore`:

```gitignore
*.tfstate
*.tfstate.*
```

Terraform provider files are also excluded:

```gitignore
.terraform/
```

Sensitive variable files are excluded:

```gitignore
*.tfvars
```

This prevents Terraform state and credentials from being committed to the public repository.

## Security Considerations

The Proxmox API token is provided through a sensitive Terraform variable.

The VM password is also provided through a sensitive variable.

The provider uses:

```hcl
insecure = true
```

because the Proxmox environment uses a local/self-signed certificate.

This configuration is appropriate for the current homelab environment but should be reviewed before using the same configuration in production.

Terraform state should also be protected because state can contain sensitive infrastructure information.

## Verification

Terraform has been tested through the complete lifecycle:

```text
Terraform initialization
        ↓
Provider authentication
        ↓
Proxmox API connectivity
        ↓
Ubuntu cloud image management
        ↓
VM creation
        ↓
Terraform state tracking
        ↓
Terraform plan verification
```

The final verification produced:

```text
Success! The configuration is valid.

No changes. Your infrastructure matches the configuration.
```

## Portfolio Value

This project demonstrates practical Infrastructure as Code skills including:

* Terraform configuration
* Proxmox automation
* Cloud-init initialization
* Infrastructure parameterization
* Resource dependencies
* Terraform state management
* Sensitive variable handling
* Infrastructure validation
* Infrastructure planning
* Repeatable deployments
* Git-based infrastructure documentation

The Terraform implementation builds on the existing Proxmox, Linux, networking, Docker, monitoring, security, and documentation work in this homelab.

## Next Steps

Planned improvements include:

1. Create reusable Terraform modules.
2. Add additional VM deployment examples.
3. Introduce environment-specific variable files.
4. Add Terraform validation to CI/CD.
5. Explore AWS infrastructure provisioning.
6. Integrate Terraform into a broader Infrastructure as Code workflow.
