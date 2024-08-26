# NGWAF Edge Deployment
resource "sigsci_edge_deployment" "ngwaf_edge_site_service" {
  site_short_name = var.NGWAF_SITE
}

resource "sigsci_edge_deployment_service" "ngwaf_edge_service_link" {
  site_short_name  = var.NGWAF_SITE
  fastly_sid       = fastly_service_vcl.test_python_org.id
  activate_version = true
  percent_enabled  = 100
  depends_on = [
    sigsci_edge_deployment.ngwaf_edge_site_service,
    fastly_service_vcl.test_python_org,
    fastly_service_dictionary_items.edge_security_dictionary_items,
    fastly_service_dynamic_snippet_content.ngwaf_config_init,
    fastly_service_dynamic_snippet_content.ngwaf_config_miss,
    fastly_service_dynamic_snippet_content.ngwaf_config_pass,
    fastly_service_dynamic_snippet_content.ngwaf_config_deliver,
  ]
}

resource "sigsci_edge_deployment_service_backend" "ngwaf_edge_service_backend_sync" {
  site_short_name                   = var.NGWAF_SITE
  fastly_sid                        = fastly_service_vcl.test_python_org.id
  fastly_service_vcl_active_version = fastly_service_vcl.test_python_org.active_version
  depends_on = [
    sigsci_edge_deployment_service.ngwaf_edge_service_link,
  ]
}