provider "vultr" {
    api_key = "${file("/var/run/secrets/vultr.txt")}"
}
