job "hello-nginx" {
  datacenters = ["dc1"]
  type = "service"
  group "hello-nginx" {
    count = 3
    network {
      port "http" {
        to = 80
      }
    }
    service {
      name = "hello-nginx"
      port = "http"
    }
    task "hello-nginx" {
      driver = "docker"
      config {
        image = "nginxdemos/hello"
        ports = ["http"]
      }
    }
  }
}
