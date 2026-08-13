terraform {
  required_version = ">= 1.15.0"

  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = "~> 0.90"
    }
  }
}

provider "proxmox" {
  endpoint  = "https://192.168.1.57:8006/"
  api_token = var.proxmox_api_token
  insecure  = true
}

variable "proxmox_api_token" {
  type      = string
  sensitive = true
}

output "terraform_version_check" {
  value = "Terraform is working successfully"
}
