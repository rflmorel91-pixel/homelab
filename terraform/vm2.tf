module "terraform_test_2" {
  source = "./modules/proxmox-vm"

  vm_name               = var.vm2_name
  vm_id                 = var.vm2_id
  proxmox_node          = var.proxmox_node
  vm_cores              = var.vm2_cores
  vm_memory             = var.vm2_memory
  vm_disk_size          = var.vm2_disk_size
  vm_datastore          = var.vm_datastore
  vm_bridge             = var.vm_bridge
  terraform_vm_password = var.terraform_vm_password
  cloud_image_id        = proxmox_download_file.ubuntu_cloud_image.id
}
