data "heroku_team" "heroku" {
  name = "kitware"
}

module "django" {
  source  = "girder/django/heroku"
  version = "0.5.0"

  project_slug     = "kitware-otm"
  route53_zone_id  = data.aws_route53_zone.kitware_otm.zone_id
  heroku_team_name = data.heroku_team.heroku.name
  subdomain_name   = "app"

  heroku_postgresql_plan      = "hobby-basic"
  heroku_worker_dyno_quantity = 0
}
