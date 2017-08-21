provider "vultr" {
    api_key = "${file("/var/run/secrets/VULTR_KEY")}"
}
