# Bootcamp Repository

**Repository owner and author:** Paritosh Dwivedi

**Course:** FRE-GY 5040 Foundations of Applied Financial Engineering

The Weekly ETF Risk Monitor is a reproducible SPY pipeline that produces a next-five-session volatility forecast and an elevated-risk score for a portfolio manager's weekly review. See [`project/README.md`](project/README.md) for the full project definition.

## Folder structure

- **`homework/`** contains one self-contained graded exercise folder per stage and is pushed to GitHub.
- **`project/`** contains the cumulative Weekly ETF Risk Monitor and is pushed to GitHub.
- **`class_materials/`** contains instructor handouts, lecture notebooks, homework starters, and lecture-generated scratch files. It is stored locally, gitignored, and never pushed to GitHub.

## Homework folder rules

- Keep each stage's homework in its own subfolder, numbered to match the stage and zero-padded where applicable, such as `homework00`, `homework01`, and `homework09`.
- Each homework folder must contain only the files and subfolders that its stage uses.
- Include every file required for grading, including data artifacts when the assignment requires them.

## Class materials rules

- Keep each stage's course files in one subfolder of `class_materials/`, named exactly as the course folder, such as `class_materials/stage01_problem-framing-and-scoping/`.
- Run lecture notebooks in place from their stage folder.
- Copy a homework starter into `homework/homeworkNN/` before working on it so the original remains unchanged.
- Keep `class_materials/` local. It is gitignored and never pushed to GitHub.

## Project folder rules

- Keep project files organized and clearly named within `project/`.
- Set up the complete project folder structure in Stage 02, then fill it as the cumulative project develops.

## Homework index

| Folder | Stage | Description |
|---|---|---|
| [`homework00/`](homework/homework00/) | 00 pre-class setup | Completes local setup and the introductory Python tutorial notebook. |
| [`homework01/`](homework/homework01/) | 01 problem framing and scoping | Frames the project problem, stakeholder, useful answer, scope, assumptions, risks, and lifecycle deliverables. |
| [`homework02/`](homework/homework02/) | 02 tooling setup | Verifies the Python environment, configuration, folder scaffold, reusable configuration code, and a small SPY risk calculation. |
| [`homework03/`](homework/homework03/) | 03 python fundamentals | Applies NumPy, pandas, and reusable utilities to supplied data and saves processed summary artifacts. |
| [`homework04/`](homework/homework04/) | 04 data acquisition and ingestion | Acquires and validates SPY and S&P 500 constituent data and saves timestamped raw snapshots. |
| [`homework05/`](homework/homework05/) | 05 data storage | Compares CSV and Parquet storage with environment-driven paths, reload validation, and reusable I/O helpers. |
| [`homework06/`](homework/homework06/) | 06 data preprocessing | Loads, cleans, and saves a sample dataset while separating raw and processed data. |
| [`homework07/`](homework/homework07/) | 07 outliers and risk assumptions | Implements IQR, z-score, and winsorizing treatments, validates them against known injected shocks, and compares their effect on real SPY returns. |
| [`homework08/`](homework/homework08/) | 08 exploratory data analysis | Profiles SPY alongside the VIX through distributions, relationships, and a time-series read, with a reusable summary helper. |
| [`homework09/`](homework/homework09/) | 09 feature engineering | Builds volatility-ratio, implied-minus-realised, and one-hot regime features, each tied to a Stage 08 finding and checked against the target. |


