output "api_endpoint" {
  value       = aws_api_gateway_stage.prod.invoke_url
  description = "REST API invoke URL for the prod stage."
}

output "api_base_url" {
  value       = aws_api_gateway_stage.prod.invoke_url
  description = "REST API invoke URL including the prod stage."
}

output "api_execution_arn" {
  value       = aws_api_gateway_rest_api.backend.execution_arn
  description = "Execution ARN used for Lambda permissions."
}

output "api_key_name" {
  value       = aws_api_gateway_api_key.backend.name
  description = "Name of the API key."
}

output "bucket_name" {
  value       = aws_s3_bucket.backend.bucket
  description = "S3 bucket that stores batches and snapshots."
}

output "lambda_function_name" {
  value       = aws_lambda_function.backend.function_name
  description = "Lambda function name."
}

output "api_stage_name" {
  value       = aws_api_gateway_stage.prod.stage_name
  description = "REST API stage name."
}

output "region" {
  value       = local.region
  description = "AWS region used by the stack."
}

output "usage_plan_rate_limit" {
  value       = aws_api_gateway_usage_plan.backend.throttle_settings[0].rate_limit
  description = "Usage plan steady-state rate limit."
}

output "usage_plan_burst_limit" {
  value       = aws_api_gateway_usage_plan.backend.throttle_settings[0].burst_limit
  description = "Usage plan burst limit."
}
