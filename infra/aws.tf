resource "aws_route53_record" "ngwaf_cname" {
  zone_id = var.route53_zone_id
  name    = var.route53_record_name
  type    = "CNAME"
  ttl     = var.route53_record_ttl
  records = ["dualstack.python.map.fastly.net"]
}