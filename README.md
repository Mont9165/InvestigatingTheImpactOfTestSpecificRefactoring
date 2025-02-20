# Replication package for "Test Refactoring"
This repository provides the replication package for our study, including the source code and datasets.

## Source Code
The repository is organized as follows:


## Requirements
You can run the package using Docker or set up a local environment.

### Using Docker
- **Docker** version XXX or later
- **Docker Compose** version XXX or later

### Using a Local Environment
- **OpenJDK** XXX or later
- **Python** XXX or later<br>(See `requirements.txt` for the necessary Python libraries.)

## Preparation
If you are using Docker, build and start the containers with:
```
docker compose build
docker compose up -d
```

## Running the Code
### Data Collection (collection directory)
This component detects self-admitted technical debt (SATD) and measures software quality from specified repositories.
1. Configure `setting.json`:

   ```
2. Run the Data Collection Script:

### Analysis (analysis directory)
Analysis scripts can be executed from the repository’s top-level directory. For example, to run the analysis for Research Question 1 (RQ1), execute:
```
python3 analysis/RQ1/rq1.py
```

