variable "vm_name" {
  type = string
}

variable "vm_id" {
  type = number
}

variable "proxmox_node" {
  type = string
}

variable "vm_cores" {
  type = number
}

variable "vm_memory" {
  type = number
}

variable "vm_disk_size" {
  type = number
}

variable "vm_datastore" {
  type = string
}

variable "vm_bridge" {
  type = string
}

variable "terraform_vm_password" {
  type      = string
  sensitive = true
}

variable "cloud_image_id" {
  type = string
}
variable "vm_username" {
  type    = string
  default = "terraform"
}
