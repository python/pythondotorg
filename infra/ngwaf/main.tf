# ? TODO: this needs reorgnization :P, was jsut trying to yank out NGWAF stuff from main CDN module
#         the goal is to let cdn apply the core config, and then ingest the service ID from that
#         and apply ngwaf stuff on top THEN set up signal sciences stuff on top of that


# ! TODO: refactor this to be dynamic depending on {test,prod}.python.org
resource "fastly_service_vcl" "ngwaf_service" {
  name     = var.service_name
  activate = true

  domain {
    name    = var.USER_VCL_SERVICE_DOMAIN_NAME
    comment = "NGWAF domain"
  }

  backend {
    address           = var.USER_VCL_SERVICE_BACKEND_HOSTNAME
    name              = "ngwaf_backend"
    port              = 443
    use_ssl           = true
    ssl_cert_hostname = var.USER_VCL_SERVICE_BACKEND_HOSTNAME
    ssl_sni_hostname  = var.USER_VCL_SERVICE_BACKEND_HOSTNAME
    override_host     = var.USER_VCL_SERVICE_BACKEND_HOSTNAME
  }

  # NGWAF Dynamic Snippets
  dynamicsnippet {
    name     = "ngwaf_config_init"
    type     = "init"
    priority = 0
  }

  dynamicsnippet {
    name     = "ngwaf_config_miss"
    type     = "miss"
    priority = 9000
  }

  dynamicsnippet {
    name     = "ngwaf_config_pass"
    type     = "pass"
    priority = 9000
  }

  dynamicsnippet {
    name     = "ngwaf_config_deliver"
    type     = "deliver"
    priority = 9000
  }

  dictionary {
    name = var.Edge_Security_dictionary
  }

  product_enablement {
    bot_management = true
  }

  lifecycle {
    ignore_changes = [product_enablement]
  }
}

output "ngwaf_service_id" {
  value = fastly_service_vcl.ngwaf_service.id
}

# Fastly Service Dictionary Items
resource "fastly_service_dictionary_items" "edge_security_dictionary_items" {
  for_each = {
    for d in fastly_service_vcl.ngwaf_service.dictionary : d.name => d if d.name == var.Edge_Security_dictionary
  }
  service_id    = fastly_service_vcl.ngwaf_service.id
  dictionary_id = each.value.dictionary_id
  items = {
    Enabled : "100"
  }
}

# Fastly Service Dynamic Snippet Contents
resource "fastly_service_dynamic_snippet_content" "ngwaf_config_init" {
  for_each = {
    for d in fastly_service_vcl.ngwaf_service.dynamicsnippet : d.name => d if d.name == "ngwaf_config_init"
  }
  service_id      = fastly_service_vcl.ngwaf_service.id
  snippet_id      = each.value.snippet_id
  content         = "### Fastly managed ngwaf_config_init"
  manage_snippets = false
}

resource "fastly_service_dynamic_snippet_content" "ngwaf_config_miss" {
  for_each = {
    for d in fastly_service_vcl.ngwaf_service.dynamicsnippet : d.name => d if d.name == "ngwaf_config_miss"
  }
  service_id      = fastly_service_vcl.ngwaf_service.id
  snippet_id      = each.value.snippet_id
  content         = "### Fastly managed ngwaf_config_miss"
  manage_snippets = false
}

resource "fastly_service_dynamic_snippet_content" "ngwaf_config_pass" {
  for_each = {
    for d in fastly_service_vcl.ngwaf_service.dynamicsnippet : d.name => d if d.name == "ngwaf_config_pass"
  }
  service_id      = fastly_service_vcl.ngwaf_service.id
  snippet_id      = each.value.snippet_id
  content         = "### Fastly managed ngwaf_config_pass"
  manage_snippets = false
}

resource "fastly_service_dynamic_snippet_content" "ngwaf_config_deliver" {
  for_each = {
    for d in fastly_service_vcl.ngwaf_service.dynamicsnippet : d.name => d if d.name == "ngwaf_config_deliver"
  }
  service_id      = fastly_service_vcl.ngwaf_service.id
  snippet_id      = each.value.snippet_id
  content         = "### Fastly managed ngwaf_config_deliver"
  manage_snippets = false
}

# NGWAF Edge Deployment
resource "sigsci_edge_deployment" "ngwaf_edge_site_service" {
  site_short_name = var.NGWAF_SITE
}

resource "sigsci_edge_deployment_service" "ngwaf_edge_service_link" {
  site_short_name  = var.NGWAF_SITE
  fastly_sid       = fastly_service_vcl.ngwaf_service.id
  activate_version = true
  percent_enabled  = 100
  depends_on = [
    sigsci_edge_deployment.ngwaf_edge_site_service,
    fastly_service_vcl.ngwaf_service,
    fastly_service_dictionary_items.edge_security_dictionary_items,
    fastly_service_dynamic_snippet_content.ngwaf_config_init,
    fastly_service_dynamic_snippet_content.ngwaf_config_miss,
    fastly_service_dynamic_snippet_content.ngwaf_config_pass,
    fastly_service_dynamic_snippet_content.ngwaf_config_deliver,
  ]
}

resource "sigsci_edge_deployment_service_backend" "ngwaf_edge_service_backend_sync" {
  site_short_name                   = var.NGWAF_SITE
  fastly_sid                        = fastly_service_vcl.ngwaf_service.id
  fastly_service_vcl_active_version = fastly_service_vcl.ngwaf_service.active_version
  depends_on = [
    sigsci_edge_deployment_service.ngwaf_edge_service_link,
  ]
}