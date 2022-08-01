data "aws_ami" "node_ami" {
  most_recent = true
  name_regex  = "^otm-worker-\\d{14}$"
  owners      = ["self"]
}

resource "aws_instance" "worker" {
  ami           = data.aws_ami.node_ami.id
  instance_type = "r5a.2xlarge"
  user_data     = file("user-data.sh")
}
