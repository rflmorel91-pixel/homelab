variable "proxmox_api_token" {
  type      = string
  sensitive = true
}

variable "terraform_vm_password" {
  type      = string
  sensitive = true
}

variable "vm_name" {
  type    = string
  default = "terraform-test"
}

variable "vm_id" {
  type    = number
  default = 101
}

variable "vm_cores" {
  type    = number
  default = 2
}

variable "vm_memory" {
  type    = number
  default = 2048
}

variable "vm_disk_size" {
  type    = number
  default = 20
}

variable "vm_bridge" {
  type    = string
  default = "vmbr0"
}

variable "proxmox_node" {
  type    = string
  default = "proxmox"
}

variable "vm_datastore" {
  type    = string
  default = "local-lvm"
}

variable "image_datastore" {
  type    = string
  default = "local"
}
