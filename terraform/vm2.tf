resource "proxmox_virtual_environment_vm" "terraform_test_2" {
  name      = "terraform-test-2"
  vm_id     = 102
  node_name = var.proxmox_node

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
    datastore_id = var.vm_datastore
    interface    = "scsi0"
    size         = 20
    file_id      = proxmox_download_file.ubuntu_cloud_image.id
  }

  network_device {
    bridge = var.vm_bridge
  }
}
