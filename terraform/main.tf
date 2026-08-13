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

variable "vm_name" {
  type    = string
  default = "terraform-test"
}

variable "vm_id" {
  type    = number
  default = 101
}

variable "vm_cores" {
  type    = number
  default = 2
}

variable "vm_memory" {
  type    = number
  default = 2048
}

variable "vm_disk_size" {
  type    = number
  default = 20
}

variable "vm_bridge" {
  type    = string
  default = "vmbr0"
}

output "terraform_version_check" {
  value = "Terraform is working successfully"
}

output "vm_id" {
  value = proxmox_virtual_environment_vm.terraform_test.vm_id
}

output "vm_name" {
  value = proxmox_virtual_environment_vm.terraform_test.name
}

output "vm_node" {
  value = proxmox_virtual_environment_vm.terraform_test.node_name
}

output "vm_mac_address" {
  value = proxmox_virtual_environment_vm.terraform_test.mac_addresses[0]
}

resource "proxmox_virtual_environment_vm" "terraform_test" {
  name      = var.vm_name
  vm_id     = var.vm_id
  node_name = "proxmox"

  cpu {
    cores = var.vm_cores
  }

  memory {
    dedicated = var.vm_memory
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
    size         = var.vm_disk_size
    file_id      = proxmox_download_file.ubuntu_cloud_image.id
  }

  network_device {
    bridge = var.vm_bridge
  }
}
resource "proxmox_download_file" "ubuntu_cloud_image" {
  content_type = "iso"
  datastore_id = "local"
  node_name    = "proxmox"

  url       = "https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img"
  file_name = "noble-server-cloudimg-amd64.img"
}
