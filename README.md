# Weather Data Analysis
![Python](https://img.shields.io/badge/python-3.13-blue)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Actions status](https://github.com/agredyaev/async-python-sprint-1/actions/workflows/app-testing.yml/badge.svg)](https://github.com/agredyaev/async-python-sprint-1/actions)
![Pydantic](https://img.shields.io/badge/Pydantic-red?logo=pydantic&logoColor=white)
![HTTPX](https://img.shields.io/badge/HTTPX-green?logo=httpx&logoColor=white)
![Polars](https://img.shields.io/badge/Polars-blue?logo=polars&logoColor=white)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Project Overview

This project analyzes weather conditions using data from the Yandex Weather API. The task involves retrieving weather data for a list of cities, calculating the average temperature and analyzing precipitation conditions for a specific period within a day.

### Key Features
- **FetchTask**: Fetches weather data from an external API (e.g., YandexWeatherAPI).
- **ExtractTask**: Extracts and validates relevant weather data.
- **TransformTask**: Processes and transforms raw weather data into structured formats.
- **AnalyzeTask**: Analyzes transformed data to compute key metrics like weather scores.

## Deploy
```bash
# clone the repository
git clone https://github.com/agredyaev/async-python-sprint-1.git
cd async-python-sprint-1
# setup the environment
make setup
# activate the virtual environment
. ./.venv/bin/activate
# run the app
make run
# run the tests
make test
```
