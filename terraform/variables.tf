variable "cert_arn" {
    type    = string
}

variable "frontend_container" {
    type    = string

    default = "ghcr.io/magfest/tuber:frontend"
}

variable "backend_container" {
    type    = string
    default = "ghcr.io/magfest/tuber:backend"
}
