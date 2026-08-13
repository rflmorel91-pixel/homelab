terraform {
  required_providers {
    proxmox = {
      source = "bpg/proxmox"
    }
  }
}

resource "proxmox_virtual_environment_vm" "this" {
  name      = var.vm_name
  vm_id     = var.vm_id
  node_name = var.proxmox_node

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
    datastore_id = var.vm_datastore
    interface    = "scsi0"
    size         = var.vm_disk_size
    file_id      = var.cloud_image_id
  }

  network_device {
    bridge = var.vm_bridge
  }
}
