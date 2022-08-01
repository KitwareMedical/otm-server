locals {
  timestamp = regex_replace(timestamp(), "[- TZ:]", "")
}

packer {
  required_plugins {
    amazon = {
      version = ">= 0.0.2"
      source  = "github.com/hashicorp/amazon"
    }
  }
}

source "amazon-ebs" "ubuntu" {
  ami_name = "otm-worker-${local.timestamp}"

  # High memory ec2 instance
  instance_type = "r5a.2xlarge"

  region = "us-east-1"

  # Ubuntu 20.04 base AMI for us-east-1
  source_ami   = "ami-083654bd07b5da81d"
  ssh_username = "ubuntu"
}

build {
  name = "main"
  sources = [
    "source.amazon-ebs.ubuntu"
  ]

  provisioner "ansible" {
    playbook_file = "${path.root}/../ansible/playbook.yml"
    galaxy_file   = "${path.root}/../ansible/requirements.yml"
  }
}
