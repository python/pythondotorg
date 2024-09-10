resource "fastly_service_vcl" "ngwaf_service" {
  count    = var.activate_ngwaf_service ? 1 : 0
  name     = "${var.name}-ngwaf"
  activate = var.activate_ngwaf_service

  domain {
    name    = var.domain
    comment = "NGWAF domain"
  }

  backend {
    address           = var.backend_address
    name              = "ngwaf_backend"
    port              = 443
    use_ssl           = true
    ssl_cert_hostname = var.backend_address
    ssl_sni_hostname  = var.backend_address
    override_host     = var.backend_address
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
    name = var.edge_security_dictionary
  }

  product_enablement {
    bot_management = true
  }

  lifecycle {
    ignore_changes = [product_enablement]
  }
}

output "ngwaf_service_id" {
  value = var.activate_ngwaf_service ? fastly_service_vcl.ngwaf_service[0].id : null
}

# Fastly Service Dictionary Items
resource "fastly_service_dictionary_items" "edge_security_dictionary_items" {
  count = var.activate_ngwaf_service ? 1 : 0
  service_id    = fastly_service_vcl.ngwaf_service[0].id
  dictionary_id = [for d in fastly_service_vcl.ngwaf_service[0].dictionary : d.dictionary_id if d.name == var.edge_security_dictionary][0]
  items = {
    Enabled : "100"
  }
}

# Fastly Service Dynamic Snippet Contents
resource "fastly_service_dynamic_snippet_content" "ngwaf_config_init" {
  count = var.activate_ngwaf_service ? 1 : 0
  service_id      = fastly_service_vcl.ngwaf_service[0].id
  snippet_id      = [for d in fastly_service_vcl.ngwaf_service[0].dynamicsnippet : d.snippet_id if d.name == "ngwaf_config_init"][0]
  content         = "### Fastly managed ngwaf_config_init"
  manage_snippets = false
}

resource "fastly_service_dynamic_snippet_content" "ngwaf_config_miss" {
  count = var.activate_ngwaf_service ? 1 : 0
  service_id      = fastly_service_vcl.ngwaf_service[0].id
  snippet_id      = [for d in fastly_service_vcl.ngwaf_service[0].dynamicsnippet : d.snippet_id if d.name == "ngwaf_config_miss"][0]
  content         = "### Fastly managed ngwaf_config_miss"
  manage_snippets = false
}

resource "fastly_service_dynamic_snippet_content" "ngwaf_config_pass" {
  count = var.activate_ngwaf_service ? 1 : 0
  service_id      = fastly_service_vcl.ngwaf_service[0].id
  snippet_id      = [for d in fastly_service_vcl.ngwaf_service[0].dynamicsnippet : d.snippet_id if d.name == "ngwaf_config_pass"][0]
  content         = "### Fastly managed ngwaf_config_pass"
  manage_snippets = false
}

resource "fastly_service_dynamic_snippet_content" "ngwaf_config_deliver" {
  count = var.activate_ngwaf_service ? 1 : 0
  service_id      = fastly_service_vcl.ngwaf_service[0].id
  snippet_id      = [for d in fastly_service_vcl.ngwaf_service[0].dynamicsnippet : d.snippet_id if d.name == "ngwaf_config_deliver"][0]
  content         = "### Fastly managed ngwaf_config_deliver"
  manage_snippets = false
}

# NGWAF Edge Deployment on SignalSciences.net
resource "sigsci_edge_deployment" "ngwaf_edge_site_service" {
  count           = var.activate_ngwaf_service ? 1 : 0
  provider        = sigsci.firewall
  site_short_name = var.ngwaf_site_name
}

resource "sigsci_edge_deployment_service" "ngwaf_edge_service_link" {
  count            = var.activate_ngwaf_service ? 1 : 0
  provider         = sigsci.firewall
  site_short_name  = var.ngwaf_site_name
  fastly_sid       = fastly_service_vcl.ngwaf_service[0].id
  activate_version = var.activate_ngwaf_service
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
  count                             = var.activate_ngwaf_service ? 1 : 0
  provider                          = sigsci.firewall
  site_short_name                   = var.ngwaf_site_name
  fastly_sid                        = fastly_service_vcl.ngwaf_service[0].id
  fastly_service_vcl_active_version = fastly_service_vcl.ngwaf_service[0].active_version
  depends_on = [
    sigsci_edge_deployment_service.ngwaf_edge_service_link,
  ]
}
