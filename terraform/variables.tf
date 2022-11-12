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

variable "uber_event" {
    type    = string
}

variable "uber_api_token" {
    type    = string
}

variable "uber_api_url" {
    type    = string
}

variable "gender_map" {
    type    = string
}