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

  ssh {
    agent    = true
    username = "root"
  }
}

variable "proxmox_api_token" {
  type      = string
  sensitive = true
}

variable "terraform_vm_password" {
  type      = string
  sensitive = true
}

output "terraform_version_check" {
  value = "Terraform is working successfully"
}
resource "proxmox_virtual_environment_vm" "terraform_test" {
  name      = "terraform-test"
  node_name = "proxmox"

  cpu {
    cores = 2
  }

  memory {
    dedicated = 2048
  }

  initialization {
    user_account {
      username = "terraform"
      password = var.terraform_vm_password
    }
    ip_config {
      ipv4 {
        address = "dhcp"
      }
    }
  }

  disk {
    datastore_id = "local-lvm"
    interface    = "scsi0"
    size         = 20
    file_id      = proxmox_download_file.ubuntu_cloud_image.id
  }

  network_device {
    bridge = "vmbr0"
  }
}
resource "proxmox_download_file" "ubuntu_cloud_image" {
  content_type = "iso"
  datastore_id = "local"
  node_name    = "proxmox"

  url       = "https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img"
  file_name = "noble-server-cloudimg-amd64.img"
}
