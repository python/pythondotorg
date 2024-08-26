output "testing-the_ngwaf" {
  value       = <<tfmultiline
  #### Click the URL to go to the service ####
  https://cfg.fastly.com/${fastly_service_vcl.test_python_org.id}
  #### Send a test request with curl. ####
  curl -i "https://${var.USER_VCL_SERVICE_DOMAIN_NAME}/anything/whydopirates?likeurls=theargs" -d foo=bar
  #### Send an test as cmd exe request with curl. ####
  curl -i "https://${var.USER_VCL_SERVICE_DOMAIN_NAME}/anything/myattackreq?i=../../../../etc/passwd'" -d foo=bar
  #### Troubleshoot the logging configuration if necessary. ####
  curl https://api.fastly.com/service/${fastly_service_vcl.test_python_org.id}/logging_status -H fastly-key:$FASTLY_API_KEY
  tfmultiline
  description = "Output hints on what to do next."
  depends_on = [
    sigsci_edge_deployment_service.ngwaf_edge_service_link
  ]
}