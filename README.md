# Guess Where Telegram Bot

[![Sonarcloud Status](https://sonarcloud.io/api/project_badges/measure?project=berkerol_guess-where-telegram-bot&metric=alert_status)](https://sonarcloud.io/dashboard?id=berkerol_guess-where-telegram-bot)
[![CI](https://github.com/berkerol/guess-where-telegram-bot/actions/workflows/lint_and_deploy.yml/badge.svg?branch=master)](https://github.com/berkerol/guess-where-telegram-bot/actions/workflows/lint_and_deploy.yml)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](https://github.com/berkerol/guess-where-telegram-bot/issues)
[![license](https://img.shields.io/badge/license-GNU%20GPL%20v3.0-blue.svg)](https://github.com/berkerol/guess-where-telegram-bot/blob/master/LICENSE)

Telegram bot that lets you guess the location of a random photo.

## Overview

You can start by sending `/random` command to receive a random photo. Then you can enter your guess and send it as a message to receive feedback (true/false). You can also use `/filter` command to filter with prefixes for intermediate directories, for example for year it will be `/filter 2022 2023`. Made with [python-telegram-bot](https://python-telegram-bot.org/). Inspired by another game of mine [guess-where](https://github.com/berkerol/guess-where).

There are 2 scripts that use the Telegram API in 2 different ways.

* `guess_where_telegram_bot.py`: This is using the polling method (fetching new messages from Telegram API periodically) with python-telegram-bot library (`getUpdates`). It needs to be run on a server (e.g. AWS EC2).
* `guess_where_telegram_bot_lambda_function.py`: This is used as a webhook that will be called by Telegram to receive new messages. It needs to be run as a function (e.g. AWS Lambda).

## Polling (`guess_where_telegram_bot.py`)

### Installation & Usage

```sh
pipenv install
pipenv shell # without this you can also do: pipenv run python3 guess_where_telegram_bot.py
python3 guess_where_telegram_bot.py
```

### Prerequisites

Following environment variables have to be set.

* S3_BUCKET
* S3_BUCKET_PREFIX
* AWS_ACCESS_KEY
* AWS_SECRET_ACCESS_KEY
* TELEGRAM_BOT_TOKEN

## Webhook (`guess_where_telegram_bot_lambda_function.py`)

### Usage

It is using the following AWS services.

* **Lambda** to run the Python script
* **DynamoDB** to store the last location and current filter
* **S3** to store the current set of paths of photos in a JSON file
* **Systems Manager Parameter Store** to store the `TELEGRAM_BOT_TOKEN`
* **CloudWatch** to store the logs

### Prerequisites

AWS services need to be set as following.

* **Lambda** function
  * Name: `guess-where-telegram-bot`
  * Runtime: `Python 3.12`
  * Architecture: `arm64`
  * Layers: `AWS-Parameters-and-Secrets-Lambda-Extension-Arm64`
  * Execution role that has access to DynamoDB, S3, Systems Manager Parameter Store, CloudWatch
  * Function URL: enabled
  * Environment variables: `S3_BUCKET`, `S3_BUCKET_PREFIX`, `PARAMETERS_SECRETS_EXTENSION_LOG_LEVEL`
* **DynamoDB** table
  * Name: `guess-where-telegram-bot`
  * Partition key: `chat_id` (string)
* **S3** bucket
  * Name: same as `S3_BUCKET` variable
* **Systems Manager Parameter Store** parameter
  * Name: `/guess-where-telegram-bot/TELEGRAM_BOT_TOKEN`
  * Type: `SecureString`

Telegram webhook needs to be set as following.

```
POST https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook?url={LAMBDA_FUNCTION_URL}
```

## Photo Structure

Photos can only be read if they are structured in a specific way.

### Directories by city as last directory

`{PATH}/{COUNTRY}/{CITY}/**/{PHOTO}.jpg`

City or country directory name should be guessed. `{COUNTRY}` **DOESN'T** have to be country, it can be anything. It is just my current setup. `**` in between can contain any number of directories from 0 to N.

### Directory by city as last element

`{PATH}/{DATE} - {ORDER} - {COUNTRY} - {CITY}/**/{PHOTO}.jpg`

City or country name should be guessed. `{DATE} - {ORDER} - {COUNTRY}` part **DOESN'T** have to be in that structure as long as elements are separated with ` - ` and city is the last element. It is just my current setup. `**` in between can contain any number of directories from 0 to N.

## Photo Source

Photos can be read from S3 bucket.

### S3 Bucket

Use with or without prefix, for example `s3://{BUCKET}` or `s3://{BUCKET}/{PREFIX}/`

There must be at least one directory between bucket and photo directories in your structure, for example `s3://{BUCKET}/Photos/{COUNTRY}/{CITY}/**/{PHOTO}.jpg` or `s3://{BUCKET}/Photos/2022/{DATE} - {ORDER} - {COUNTRY} - {CITY}/**/{PHOTO}.jpg`

## References

* [boto3 S3](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)

## Continous Integration

It is setup using GitHub Actions in `lint` job in `.github/workflows/lint_and_deploy.yml`

## Continuous Delivery

`guess_where_telegram_bot_lambda_function.py` is deployed to AWS Lambda automatically using GitHub Actions in `deploy` job in `.github/workflows/lint_and_deploy.yml`

## Contribution

Feel free to [contribute](https://github.com/berkerol/guess-where-telegram-bot/issues).

## Distribution

You can distribute this software freely under [GNU GPL v3.0](https://github.com/berkerol/guess-where-telegram-bot/blob/master/LICENSE).
