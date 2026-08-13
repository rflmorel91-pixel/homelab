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
