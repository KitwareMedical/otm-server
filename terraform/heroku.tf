data "heroku_team" "heroku" {
  name = "kitware"
}

module "django" {
  source  = "girder/django/heroku"
  version = "0.8.0"

  project_slug     = "kitware-otm"
  route53_zone_id  = data.aws_route53_zone.kitware_otm.zone_id
  heroku_team_name = data.heroku_team.heroku.name
  subdomain_name   = "app"

  heroku_postgresql_plan      = "hobby-basic"
  heroku_worker_dyno_quantity = 0

  # worker
  ec2_worker_instance_quantity = 1
  ec2_worker_instance_type     = "r5a.2xlarge"
  ec2_worker_ssh_public_key    = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILvUQxv4YjuI67JMxxsH+Cq5puATcZKhNf5RbryMo9ui jjnesbitt2@gmail.com"
  ec2_worker_volume_size       = "64"
}
