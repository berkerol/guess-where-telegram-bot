# Guess Where Telegram Bot

[![Sonarcloud Status](https://sonarcloud.io/api/project_badges/measure?project=berkerol_guess-where-telegram-bot&metric=alert_status)](https://sonarcloud.io/dashboard?id=berkerol_guess-where-telegram-bot)
[![CI](https://github.com/berkerol/guess-where-telegram-bot/actions/workflows/lint.yml/badge.svg?branch=master)](https://github.com/berkerol/guess-where-telegram-bot/actions/workflows/lint.yml)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](https://github.com/berkerol/guess-where-telegram-bot/issues)
[![license](https://img.shields.io/badge/license-GNU%20GPL%20v3.0-blue.svg)](https://github.com/berkerol/guess-where-telegram-bot/blob/master/LICENSE)

Telegram bot that lets you guess the location of a random photo.

## Overview

You can start by sending `/random` command to receive a random photo. Then you can enter your guess and send it as a message to receive feedback (true/false). Made with [python-telegram-bot](https://python-telegram-bot.org/). Inspired by another game of mine [guess-where](https://github.com/berkerol/guess-where).

## Installation & Usage

```sh
pipenv install
pipenv shell # without this you can also do: pipenv run python3 guess_where_telegram_bot.py
python3 guess_where_telegram_bot.py
```

## Prerequisites

Following environment variables have to be set:

* S3_BUCKET
* S3_BUCKET_PREFIX
* AWS_ACCESS_KEY
* AWS_SECRET_ACCESS_KEY
* TELEGRAM_BOT_TOKEN

## Photo Structure

Photos can only be read if they are structured in a specific way.

### Directories by city as last directory

`{PATH}/{COUNTRY}/{CITY}/**/{PHOTO}.jpg`

City directory name should be guessed. `{COUNTRY}` **DOESN'T** have to be country, it can be anything. It is just my current setup. `**` in between can contain any number of directories from 0 to N.

### Directory by city as last element

`{PATH}/{DATE} - {ORDER} - {COUNTRY} - {CITY}/**/{PHOTO}.jpg`

City name should be guessed. `{DATE} - {ORDER} - {COUNTRY}` part **DOESN'T** have to be in that structure as long as elements are separated with ` - ` and city is the last element. It is just my current setup. `**` in between can contain any number of directories from 0 to N.

## Photo Source

Photos can be read from S3 bucket.

### S3 Bucket

Use with or without prefix, for example `s3://{BUCKET}` or `s3://{BUCKET}/{PREFIX}/`

There must be at least one directory between bucket and photo directories in your structure, for example `s3://{BUCKET}/Photos/{COUNTRY}/{CITY}/**/{PHOTO}.jpg` or `s3://{BUCKET}/Photos/2022/{DATE} - {ORDER} - {COUNTRY} - {CITY}/**/{PHOTO}.jpg`

## References

* [boto3 S3](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)

## Continous Integration

It is setup using GitHub Actions in `.github/workflows/lint.yml`

## Contribution

Feel free to [contribute](https://github.com/berkerol/guess-where-telegram-bot/issues).

## Distribution

You can distribute this software freely under [GNU GPL v3.0](https://github.com/berkerol/guess-where-telegram-bot/blob/master/LICENSE).
