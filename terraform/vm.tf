module "terraform_test" {
  source = "./modules/proxmox-vm"

  vm_name               = var.vm_name
  vm_id                 = var.vm_id
  proxmox_node          = var.proxmox_node
  vm_cores              = var.vm_cores
  vm_memory             = var.vm_memory
  vm_disk_size          = var.vm_disk_size
  vm_datastore          = var.vm_datastore
  vm_bridge             = var.vm_bridge
  terraform_vm_password = var.terraform_vm_password
  vm_username           = "terraform"
  cloud_image_id        = proxmox_download_file.ubuntu_cloud_image.id
}
