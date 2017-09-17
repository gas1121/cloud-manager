provider "digitalocean" {
    token = "${file("/var/run/secrets/DIGITALOCEAN_TOKEN")}"
}
