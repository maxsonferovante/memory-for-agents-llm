variable "name_prefix" {
  description = "Prefix for all backend resource names."
  type        = string
  default     = "claude-memory"
}

variable "aws_region" {
  description = "AWS region for the backend."
  type        = string
  default     = null
}

variable "lambda_zip_path" {
  description = "Path to the built Lambda zip archive."
  type        = string
}

variable "api_key_value" {
  description = "API key value used by the REST API."
  type        = string
  sensitive   = true
}

variable "usage_plan_rate_limit" {
  description = "Steady-state requests per second allowed by the usage plan."
  type        = number
  default     = 10
}

variable "usage_plan_burst_limit" {
  description = "Burst requests allowed by the usage plan."
  type        = number
  default     = 20
}

variable "backend_auth_token" {
  description = "Optional bearer token required by the Lambda."
  type        = string
  default     = null
  sensitive   = true
}
