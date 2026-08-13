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
variable "ubuntu_image_url" {
  type    = string
  default = "https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img"
}

variable "ubuntu_image_file_name" {
  type    = string
  default = "noble-server-cloudimg-amd64.img"
}
variable "vm2_name" {
  type    = string
  default = "terraform-test-2"
}

variable "vm2_id" {
  type    = number
  default = 102
}

variable "vm2_cores" {
  type    = number
  default = 2
}

variable "vm2_memory" {
  type    = number
  default = 2048
}

variable "vm2_disk_size" {
  type    = number
  default = 20
}
