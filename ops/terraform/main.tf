
terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.38"
    }
  }
  required_version = ">= 1.5.0"
}

provider "digitalocean" {
  token = var.do_token
}

variable "do_token" {}
variable "region" { default = "nyc3" }
variable "droplet_size" { default = "s-2vcpu-4gb" }
variable "domain" {}

resource "digitalocean_droplet" "otp" {
  name   = "official-trades-pro"
  region = var.region
  size   = var.droplet_size
  image  = "docker-20-04"
  ipv6   = true
  monitoring = true
  user_data = templatefile("${path.module}/user_data.sh", {
    domain = var.domain
  })
}

output "droplet_ip" { value = digitalocean_droplet.otp.ipv4_address }
