data "heroku_team" "heroku" {
  name = "kitware"
}

module "django" {
  source  = "girder/girder4/heroku"
  version = "0.12.0"

  heroku_team_name = data.heroku_team.heroku.name
  project_slug     = "kitware-otm"
  route53_zone_id  = data.aws_route53_zone.kitware_otm.zone_id
  subdomain_name   = "app"

  heroku_app_name                    = "otm-kitware"
  heroku_postgresql_plan             = "standard-0"
  heroku_cloudamqp_plan              = "squirrel-1"
  heroku_worker_dyno_quantity        = 0
  django_cors_origin_whitelist       = ["https://otm-client.pages.dev"]
  django_cors_origin_regex_whitelist = ["^https:\\/\\/[0-9a-z]+\\.otm-client.pages.dev$"]
}
