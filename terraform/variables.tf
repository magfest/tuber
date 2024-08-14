variable "cert_arn" {
    type    = string
}

variable "frontend_container" {
    type    = string

    default = "ghcr.io/magfest/tuber-frontend"
}

variable "backend_container" {
    type    = string
    default = "ghcr.io/magfest/tuber-backend"
}

variable "TFC_CONFIGURATION_VERSION_GIT_COMMIT_SHA" {
    type    = string
    default = "latest"
}

variable "gender_map" {
    type    = string
}

variable "db_security_groups" {
    type    = list(string)
    default = []
}