# Task Scheduling System

![Python](https://img.shields.io/badge/python-3.13-blue)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Actions status](https://github.com/agredyaev/async-python-sprint-1/actions/workflows/app-testing.yml/badge.svg)](https://github.com/agredyaev/async-python-sprint-1/actions)
![Pydantic](https://img.shields.io/badge/Pydantic-red?logo=pydantic&logoColor=white)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](https://mit-license.org/)

This project implements a flexible and efficient task scheduling system in Python. It's designed to handle various types of tasks, manage their execution, and provide a robust framework for complex task pipelines.

## Key Features

- **Modular Architecture**: The system is built with a modular design, allowing easy extension and customization.
- **Multiple Task Types**: Supports different task types, including file operations and HTTP requests.
- **Context Management**: Provides a context system for sharing data between tasks and tracking execution state.
- **State Persistence**: Implements a file-based state manager for reliable task state storage and recovery.
- **Asynchronous Execution**: Uses Python generators for non-blocking task execution.
- **Priority Scheduling**: Tasks can be assigned priorities for optimized execution order.
- **Dependency Management**: Supports task dependencies, ensuring proper execution order in complex workflows.
- **Error Handling and Retries**: Includes built-in error handling and configurable retry mechanisms.
- **Extensible Task Registry**: Allows easy registration and creation of new task types.

[Docs](/docs/classes_schema.md)

![PlantUML](https://www.plantuml.com/plantuml/dpng/hLLTRzem57tFht3JFO1K6jHjVPY4L4g9Dcbj4Q7h8pBn9KGaJkRhbA9f_tssWqdmM8UcyHJVZtlEFJvkRr1I8QiyyyvI7cSL0xAIiiHFGI3evZ99vQfQL0WYBhW4BY_Z8W_AZ7BTqqF9idGHZ3xq9ZhqTFyro2bA42eq7waEcd8GbwMUxvqnMAeZkHj_-p9wV8XE099LIPbutm2cAjjRgeeUbYALW1QFmOlEuHubV7oO3P_7qUFz-By2cHZT01Ovz3usgjcjWd8hLmMlTxRPDfj0KbpZ6_bbci4RQGvoKuZrV9CAO3jfSPtoaWgQ4r5Kd8qAmK6GgtuhiQ3nEjbbiqAGyp0CXs6xGkbG5XouZEGs0w86NtdUaB5n1hcApcZIyL4MWYRWNv1tkA8b3APw8h3RuZNIvqvNPHQ9WHZuv-FhyNKurDLQDXljcv_VTOVl2PmwFkoh9Vf_7Ez5MvIGps_r42gs7OnNmAeCn1nDveBuCufh4jNnb2UaRl6xv8T7r6_luQPNDKNssrU7YRbl_NLFkT86YTGpuHNYIgO59vGpWdi4pRQsrC2lhQ8ZaYOuQ0dGTT3roBc094KfjfRsT7S-P557GQ01ZWLGQJcb72NbCM2RXCxWAHpCUtcLyrolQNGOrH5Y5ZzHZTqK_3STK589BGQHFf-0R_fgHKeGg0LIEfpAuP34tQAZd-XyznOKLAYE9B9FmvwDa_HHPuuGKR4gEnH2psqex00KWP-UDuMixK7N4AFMFQFgSCgTkslaiPaZFLPhjyF4RRrJv0Wp1SemU1Qfj7sgpVGv_DklQoAAbvIvdhM0xYP7Mt_tcyPjR6Hewl7silHxyksxccrBC5u2iIn4ZcOhKfGWg1vv_CPSqxJGzByVY_PvDfly1SsK2FXU0Hwwu-0l_p7GuzesorgRM2sTGitJARGZcnb7hFHKCbrhCxlXUjhfBQx1NIT5z0Kmc8AEjBnq0vnLUVOB)

## Deploy
```bash
# clone the repository
git clone https://github.com/agredyaev/async-python-sprint-2.git
cd async-python-sprint-2
# setup the environment
make setup
# activate the virtual environment
. ./.venv/bin/activate
# run the app
make run
# run the tests
make test
```
