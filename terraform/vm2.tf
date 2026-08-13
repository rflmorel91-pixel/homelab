resource "proxmox_virtual_environment_vm" "terraform_test_2" {
  name      = var.vm2_name
  vm_id     = var.vm2_id
  node_name = var.proxmox_node

  cpu {
    cores = var.vm2_cores
  }

  memory {
    dedicated = var.vm2_memory
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
    size         = var.vm2_disk_size
    file_id      = proxmox_download_file.ubuntu_cloud_image.id
  }

  network_device {
    bridge = var.vm_bridge
  }
}
