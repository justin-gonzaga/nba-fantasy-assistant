terraform {
  required_version = ">= 1.16.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 7.0"
    }
  }

  backend "gcs" {
    bucket = "nbafa-hdfo-tfstate"
    prefix = "envs/dev"
  }
}

provider "google" {
  region = "australia-southeast1"
}

provider "google-beta" {
  region = "australia-southeast1"
}
