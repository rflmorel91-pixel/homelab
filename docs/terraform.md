# Terraform Infrastructure

## Overview

Terraform is used to provision and manage infrastructure on the Proxmox VE hypervisor.

The current implementation demonstrates Infrastructure as Code (IaC) by managing multiple Ubuntu Server virtual machines through the `bpg/proxmox` Terraform provider and a reusable Proxmox VM module.

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
   ├── VM 101: terraform-test
   ├── VM 102: terraform-test-2
   └── VM 103: terraform-test-3
```

## Terraform Environment

| Component        | Configuration             |
| ---------------- | ------------------------- |
| Terraform        | 1.15.8                    |
| Provider         | bpg/proxmox v0.111.1      |
| Hypervisor       | Proxmox VE 9.2.5          |
| Proxmox Node     | proxmox                   |
| Operating System | Ubuntu Server cloud image |
| Network          | vmbr0                     |
| IP Configuration | DHCP                      |

## Managed Virtual Machines

| VM ID | VM Name          | CPU | Memory  | Disk  |
| ----- | ---------------- | --- | ------- | ----- |
| 101   | terraform-test   | 2   | 2048 MB | 20 GB |
| 102   | terraform-test-2 | 2   | 2048 MB | 20 GB |
| 103   | terraform-test-3 | 2   | 2048 MB | 20 GB |

All three virtual machines are provisioned from the same reusable Terraform module.

## Project Structure

```text
terraform/
├── main.tf
├── vm.tf
├── vm2.tf
├── vm3.tf
├── variables.tf
├── outputs.tf
├── terraform.tfvars
├── .terraform.lock.hcl
└── modules/
    └── proxmox-vm/
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

### `main.tf`

Contains the Terraform version requirement, provider configuration, Proxmox authentication, and Ubuntu cloud-image resource.

### `vm.tf`

Calls the reusable `proxmox-vm` module to manage VM 101.

### `vm2.tf`

Calls the reusable `proxmox-vm` module to manage VM 102.

### `vm3.tf`

Calls the reusable `proxmox-vm` module to manage VM 103.

## Reusable Terraform Module

The `modules/proxmox-vm/` directory contains the reusable Proxmox VM module.

### `modules/proxmox-vm/main.tf`

Defines the Proxmox virtual machine resource used by each module instance.

The module handles:

* VM name
* VM ID
* Proxmox node
* CPU allocation
* Memory allocation
* Disk configuration
* Network bridge
* Ubuntu cloud image
* Cloud-init initialization
* VM username
* VM password

### `modules/proxmox-vm/variables.tf`

Defines the configurable inputs used by the module.

The VM username is parameterized with a default value of:

```hcl
terraform
```

This allows the module to be reused without hard-coding the username into the VM resource.

### `modules/proxmox-vm/outputs.tf`

Provides useful deployment information including:

* VM ID
* VM name
* Proxmox node
* VM MAC address

## Infrastructure as Code Workflow

Changes are managed using the standard Terraform workflow:

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

Current validation result:

```text
Success! The configuration is valid.
```

### Planning

```bash
terraform plan
```

Compares the desired configuration against the current Terraform state and real infrastructure.

Current verification result:

```text
No changes. Your infrastructure matches the configuration.
```

### Applying

```bash
terraform apply
```

Applies approved infrastructure changes.

Terraform has successfully created and manages all three test virtual machines.

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

### State Migration

During the conversion from standalone VM resources to reusable modules, Terraform state was migrated using `terraform state mv`.

This allowed existing Proxmox VMs to become managed by the new module addresses without destroying and recreating the virtual machines.

The final Terraform state contains:

```text
proxmox_download_file.ubuntu_cloud_image
module.terraform_test.proxmox_virtual_environment_vm.this
module.terraform_test_2.proxmox_virtual_environment_vm.this
module.terraform_test_3.proxmox_virtual_environment_vm.this
```

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
Reusable module deployment
        ↓
Terraform state migration
        ↓
Terraform state tracking
        ↓
Terraform validation
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
* Reusable Terraform modules
* Cloud-init initialization
* Infrastructure parameterization
* Resource dependencies
* Terraform state management
* Terraform state migration
* Sensitive variable handling
* Infrastructure validation
* Infrastructure planning
* Repeatable deployments
* Git-based infrastructure documentation

The Terraform implementation builds on the existing Proxmox, Linux, networking, Docker, monitoring, security, and documentation work in this homelab.

## 90-Day IT Program Alignment

This project advances the automation phase of the homelab-to-IT-business roadmap:

```text
Build
  ↓
Document
  ↓
Automate  ← Terraform milestone
  ↓
Demonstrate
  ↓
Package
  ↓
Sell
```

Terraform converts the existing manually configured Proxmox environment into repeatable Infrastructure as Code.

This creates a practical foundation for future infrastructure services such as:

* Proxmox VM deployment
* Linux server provisioning
* Repeatable infrastructure builds
* Infrastructure documentation
* Configuration standardization
* Automated client environments

## Next Steps

Planned improvements include:

1. Add Terraform validation to CI/CD.
2. Introduce environment-specific variable files.
3. Improve module documentation and examples.
4. Explore AWS infrastructure provisioning.
5. Extend the Infrastructure as Code workflow beyond the Proxmox homelab.
6. Connect Terraform skills to future infrastructure service packages.
