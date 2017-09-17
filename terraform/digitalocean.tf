provider "digitalocean" {
    token = "${file("/var/run/secrets/digitalocean.txt")}"
}
