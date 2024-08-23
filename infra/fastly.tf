# Fastly VCL Service
resource "fastly_service_vcl" "frontend-vcl-service" {
  name = "NGWAF Testing"

  domain {
    name    = var.USER_VCL_SERVICE_DOMAIN_NAME
    comment = "NGWAF testing"
  }

  backend {
    address           = var.USER_VCL_SERVICE_BACKEND_HOSTNAME
    name              = "vcl_service_origin_1"
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

  lifecycle {
    ignore_changes = [product_enablement]
  }

  force_destroy = true
}

# Fastly Service Dictionary Items
resource "fastly_service_dictionary_items" "edge_security_dictionary_items" {
  for_each = {
    for d in fastly_service_vcl.frontend-vcl-service.dictionary : d.name => d if d.name == var.Edge_Security_dictionary
  }
  service_id    = fastly_service_vcl.frontend-vcl-service.id
  dictionary_id = each.value.dictionary_id
  items = {
    Enabled: "100"
  }
}

# Fastly Service Dynamic Snippet Contents
resource "fastly_service_dynamic_snippet_content" "ngwaf_config_init" {
  for_each = {
    for d in fastly_service_vcl.frontend-vcl-service.dynamicsnippet : d.name => d if d.name == "ngwaf_config_init"
  }
  service_id      = fastly_service_vcl.frontend-vcl-service.id
  snippet_id      = each.value.snippet_id
  content         = "### Fastly managed ngwaf_config_init"
  manage_snippets = false
}

resource "fastly_service_dynamic_snippet_content" "ngwaf_config_miss" {
  for_each = {
    for d in fastly_service_vcl.frontend-vcl-service.dynamicsnippet : d.name => d if d.name == "ngwaf_config_miss"
  }
  service_id      = fastly_service_vcl.frontend-vcl-service.id
  snippet_id      = each.value.snippet_id
  content         = "### Fastly managed ngwaf_config_miss"
  manage_snippets = false
}

resource "fastly_service_dynamic_snippet_content" "ngwaf_config_pass" {
  for_each = {
    for d in fastly_service_vcl.frontend-vcl-service.dynamicsnippet : d.name => d if d.name == "ngwaf_config_pass"
  }
  service_id      = fastly_service_vcl.frontend-vcl-service.id
  snippet_id      = each.value.snippet_id
  content         = "### Fastly managed ngwaf_config_pass"
  manage_snippets = false
}

resource "fastly_service_dynamic_snippet_content" "ngwaf_config_deliver" {
  for_each = {
    for d in fastly_service_vcl.frontend-vcl-service.dynamicsnippet : d.name => d if d.name == "ngwaf_config_deliver"
  }
  service_id      = fastly_service_vcl.frontend-vcl-service.id
  snippet_id      = each.value.snippet_id
  content         = "### Fastly managed ngwaf_config_deliver"
  manage_snippets = false
}