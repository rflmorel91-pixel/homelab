module "terraform_test_3" {
  source = "./modules/proxmox-vm"

  vm_name               = "terraform-test-3"
  vm_id                 = 103
  proxmox_node          = var.proxmox_node
  vm_cores              = 2
  vm_memory             = 2048
  vm_disk_size          = 20
  vm_datastore          = var.vm_datastore
  vm_bridge             = var.vm_bridge
  terraform_vm_password = var.terraform_vm_password
  cloud_image_id        = proxmox_download_file.ubuntu_cloud_image.id
}
