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
output "vm2_id" {
  value = proxmox_virtual_environment_vm.terraform_test_2.vm_id
}

output "vm2_name" {
  value = proxmox_virtual_environment_vm.terraform_test_2.name
}

output "vm2_node" {
  value = proxmox_virtual_environment_vm.terraform_test_2.node_name
}

output "vm2_mac_address" {
  value = proxmox_virtual_environment_vm.terraform_test_2.mac_addresses[0]
}
