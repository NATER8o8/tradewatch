
terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

provider "digitalocean" {
  token = var.do_token
}

variable "do_token" {}
variable "region" { default = "nyc3" }
variable "size" { default = "s-2vcpu-4gb" }

resource "digitalocean_droplet" "otp" {
  image  = "docker-20-04"
  name   = "official-trades-pro"
  region = var.region
  size   = var.size
  ssh_keys = [ var.ssh_fingerprint ]
}

variable "ssh_fingerprint" {}

output "droplet_ip" {
  value = digitalocean_droplet.otp.ipv4_address
}
