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
