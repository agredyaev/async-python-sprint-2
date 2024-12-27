# Task Scheduling System

![Python](https://img.shields.io/badge/python-3.13-blue)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Actions status](https://github.com/agredyaev/async-python-sprint-2/actions/workflows/app-testing.yml/badge.svg)](https://github.com/agredyaev/async-python-sprint-2/actions)
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

![PlantUML](https://www.plantuml.com/plantuml/dpng/hLLDZ-964BtxL_HwSm1f6QDDieT8ICkoM8cKsK6OpHnHuouR2xljTBM7GL7-UxfiDpRsYFYmdAYFUg_wzMluZ9ehNMQfyowHOLeAO4Uj2_pDynG_FyI9FfQ74a65kTGWzKEOPrwHSaapCzGYJGxUwfVPXbBV7__qCeuQb4djLsQ29nBKGq7upZi1aGdPr_LVVwoUlWKZY7HPSA5-RWaJKvr5fcE6XKeqeEKJy48rlBBuJzzso-TryFIu_g54LOwV0VCCPhzQrTfJUSL57tDPdzbMkzjuckC9xzIZ98KxPGdwdAlJ_fme48sqU4famHNFcCfBALQvag3OntcdSE3XAMwgQQxOUz_tbtwtm-XGv1Aa3lGb1MQ0FphEKeXr2fd9xdWySL7dYiVWVc0_uP4NiDWI8eWl-Mj0yMHgAeUuebYuxzUVrf_y9NMJR3Oxhpxkj0z-NM0il3ytXvYFXIVTno97y-WGHUCNbnfUzMZmA9hV0NUSu88QilqNGk7gCi7m2A9CGUsngdnWxiuSXWLrFf4ngqVSAVl7OUPpVNljh1aAx7VN19lAf_JjaKiU0p9DcF0AOQcJN38k1SCh0wrRFuM5MrkSCfh7kEXStBJ7Jf1x1N62MbtisjicljsYpeB2YZXKmBNTAP6ekGm1kqjG1TiTA1pGDnUpp-Y4bGIhEiFgCuyJea71-n9Gpr00r5n3Xp-WU0HxDLTBKO12KiO8CFOIRfVuUfZGRyg-URo6oZSX2-nRjd5b8GgfyiOY9bUcjp8GRhj2Gs0M-DTnjf1spTTtmgfpmMWcUks3cxFosCfmfbvrE57dRN-lgIVC5hX0xrabsiwPCPhhExdxh3OgVqb4twoMi7-IjqS7RYFUraRLcWHlBsj7ThSFQdSfW88Dg2XN6LQdOda1YXFayCRwhwObehzAI_JxRhVv7wAgHS7V9U2jCMx-fNfyRolQ7j6QmohOQwGLUuqMieCnDD3tGb2lhJJWX3P-f6_hldy2_WBeRO4o7GTz1YdABFqF)

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
