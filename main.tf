provider "aws" {
  region = "eu-central-1"
}

variable "bucket_name" {
  description = "The name of the S3 bucket"
  type        = string
}

resource "aws_iam_role" "iam_role" {
  name               = "guess-where-telegram-bot-role-3ytihhvk"
  assume_role_policy = data.aws_iam_policy_document.assume_role_policy.json
  path               = "/service-role/"
}

data "aws_iam_policy_document" "assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "execution_role" {
  policy_arn = "arn:aws:iam::643987649376:policy/service-role/AWSLambdaBasicExecutionRole-42b92673-7cdf-4239-bd87-134d6a7b6ac8"
  role       = aws_iam_role.iam_role.name
}

resource "aws_iam_role_policy_attachment" "dynamodb_full_access" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
  role       = aws_iam_role.iam_role.name
}

resource "aws_iam_role_policy_attachment" "s3_full_access" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
  role       = aws_iam_role.iam_role.name
}

resource "aws_iam_role_policy" "ssm_parameter_access" {
  name   = "GetParameterFromParameterStore"
  role   = aws_iam_role.iam_role.id
  policy = data.aws_iam_policy_document.ssm_get_parameter_policy.json
}

data "aws_iam_policy_document" "ssm_get_parameter_policy" {
  statement {
    actions   = ["ssm:GetParameter", "kms:Decrypt"]
    resources = ["*"]
    sid       = "GetParameterFromParameterStore"
  }
}

resource "aws_lambda_function" "lambda_function" {
  function_name  = "arn:aws:lambda:eu-central-1:643987649376:function:guess-where-telegram-bot"
  role           = aws_iam_role.iam_role.arn
  handler        = "guess_where_telegram_bot_lambda_function.lambda_handler"
  runtime        = "python3.12"
  architectures  = ["arm64"]
  timeout        = 60
  filename       = "placeholder.zip"
  layers         = ["arn:aws:lambda:eu-central-1:187925254637:layer:AWS-Parameters-and-Secrets-Lambda-Extension-Arm64:12"]

  environment {
    variables = {
      S3_BUCKET = var.bucket_name
      S3_BUCKET_PREFIX = "Photos/"
      PARAMETERS_SECRETS_EXTENSION_LOG_LEVEL = "WARN"
    }
  }

  lifecycle {
    ignore_changes = [filename]
  }
}

resource "aws_lambda_function_url" "lambda_function_url" {
  function_name      = aws_lambda_function.lambda_function.function_name
  authorization_type = "NONE"
}

resource "aws_dynamodb_table" "dynamodb_table" {
  name         = "guess-where-telegram-bot"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "chat_id"

  attribute {
    name = "chat_id"
    type = "S"
  }
}

resource "aws_s3_bucket" "s3_bucket" {
  bucket = var.bucket_name
}

resource "aws_ssm_parameter" "ssm_parameter" {
  name  = "/guess-where-telegram-bot/TELEGRAM_BOT_TOKEN"
  type  = "SecureString"
  value = "placeholder"

  lifecycle {
    ignore_changes = [value]
  }
}

output "lambda_function_url" {
  value = aws_lambda_function_url.lambda_function_url.function_url
}
