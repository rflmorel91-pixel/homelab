output "vm_id" {
  value = proxmox_virtual_environment_vm.this.vm_id
}

output "vm_name" {
  value = proxmox_virtual_environment_vm.this.name
}

output "vm_node" {
  value = proxmox_virtual_environment_vm.this.node_name
}

output "vm_mac_address" {
  value = proxmox_virtual_environment_vm.this.mac_addresses[0]
}
