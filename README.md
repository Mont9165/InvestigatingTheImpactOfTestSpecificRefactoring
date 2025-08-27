# Understanding Refactoring in Test Code: An Empirical Study : Replication Package

This repository contains the replication package for the paper "Understanding Refactoring in Test Code: An Empirical Study". <br>
The study analyzes test refactoring commits to understand their relationship with test smells.

## Overview

This research consists of five main phases:

1. **Data Collection**: Collecting test refactoring commits from open-source projects
2. **Sampling**: Sampling and filtering relevant commits 
3. **Manual Inspection**: Manual inspection using RefactorHub
4. **Analysis**: Statistical analysis of test refactoring impact on test smells

## Repository Structure

```
├── 1_collect_test_refactoring_commits/     # Phase 1: Collect test refactoring commits
├── 2_sampling_test_refactor_commits/       # Phase 2: Sample and filter commits
├── 3_merge_each_annotator_data_from_refactorhub/  # Phase 3: Merge annotation data
├── 4_manual_inspection/                    # Phase 4: Manual validation
├── 5_analyze_test_refactoring/            # Phase 5: Analysis and results
├── sh_scripts/                            # Shell scripts for automation
├── requirements.txt                       # Python dependencies
├── Dockerfile                            # Docker configuration
├── docker-compose.yml                    # Docker Compose configuration
├── docker-entrypoint.sh                  # Docker startup script
├── .dockerignore                         # Docker build exclusions
└── README.md                             # This file
```

## Requirements

### Using Docker (Recommended)
- **Docker** 20.10 or later
- **Docker Compose** 2.0 or later

### Using Local Environment
- **OpenJDK** 17 or later
- **Python** 3.11 or later
- **Maven** 3.6 or later

Required Python libraries are listed in `requirements.txt`:
- pandas==2.1.4
- SQLAlchemy==2.0.37
- jupyter_client==8.6.0
- GitPython==3.1.31
- seaborn==0.13.1
- matplotlib==3.8.2

## Setup

### Using Docker (Recommended)

#### Option 1: Using Docker Compose (Easiest)
1. Build and start the research environment:
   ```bash
   docker compose up -d test-refactoring-research
   ```

2. Enter the interactive container:
   ```bash
   docker compose exec test-refactoring-research bash
   ```

3. Optional: Start Jupyter notebook for interactive analysis:
   ```bash
   docker compose up -d jupyter
   # Access at http://localhost:8888
   ```

#### Option 2: Using Docker directly
1. Build the Docker image:
   ```bash
   docker build -t test-refactoring-analysis .
   ```

2. Run the container with volume mounts:
   ```bash
   docker run -it --name test-refactoring \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/results:/app/results \
     test-refactoring-analysis
   ```

### Using Local Environment
1. Install Java dependencies:
   ```bash
   cd 1_collect_test_refactoring_commits
   mvn clean compile package
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Phase 1: Collect Test Refactoring Commits
No need to run because data already exists in `1_collect_test_refactoring/src/resource/output`. If you want to re-run, use:
```bash
cd 1_collect_test_refactoring_commits
jar -xf GetCommitInformation-1.0-SNAPSHOT.jar

# Create required directories 
mkdir -p src/main/resources/input
mkdir -p src/main/resources/output  
mkdir -p src/main/resources/error

# Copy the experimental data from the source
cp ../src/main/resources/input/projects_info.csv src/main/resources/input/projects_info.csv

# Note: The projects_info.csv is experimental dataset
# with 2000+ Java projects used in our study

# Run the application
java -cp . get_refactor_commit.GetTestRefactorCommit
```

### Phase 2: Sampling Test Refactor Commits
No need to run because data already exists
```bash
cd 2_sampling_test_refactor_commits/src
# Note: The sampling_test_commits.csv, and sampling_test_commits.ndjson is experimental dataset for manual annotation
python sampling_only_modified_test_files_commits.py
python create_graph_only_modified_test_files_commits.py
```

#### Phase 3: Merge Annotation Data (No need)
```bash
cd 3_merge_each_annotator_data_from_refactorhub/src
python get_annotation_data_from_server.py
```

#### Phase 4: Manual Inspection (No need)
```bash
cd 4_manual_inspection/src
python get_refactoring_data_from_server.py
```

### Phase 5: Analysis
```bash
cd 5_analyze_test_refactoring/src/analysis

# Research Question 1: Relationship between general and test refactoring
python rq1/analyze_relationship_general_vs_test.py

# Research Question 2: Test refactoring patterns
python rq2/analyze_rq2.py

# Research Question 3: Impact on test smells
python rq3/0_descriptive_statistics.py
python rq3/1_refactoring_smell_relationship_analysis.py
```

### Test Smell Detection
The study uses TestSmellDetector to analyze test smells:
```bash
cd 5_analyze_test_refactoring
./sh/testsmell.sh
./sh/testsmell_diff.sh
```

## Key Features

- **Automated Data Collection**: Java-based tool to collect test refactoring commits from Git repositories
- **Statistical Analysis**: Comprehensive statistical analysis using Python
- **Test Smell Detection**: Integration with TestSmellDetector for analyzing test code quality
- **Visualization**: Automated generation of charts and statistical summaries
- **Docker Support**: Containerized environment for reproducible research

## Research Questions

1. **RQ1**: How frequently do test refactorings co-occur with general refactorings?
2. **RQ2**: What types of test refactoring are performed?
3. **RQ3**: Do test refactorings help reduce test smells?

## Results

Analysis results are stored in:
- `5_analyze_test_refactoring/src/analysis/rq*/`: Statistical analysis results
- `5_analyze_test_refactoring/src/results/`: Manual inspection results

[//]: # (- Generated visualizations and LaTeX tables for publication)

[//]: # (## Citation)

[//]: # ()
[//]: # (If you use this replication package in your research, please cite our paper:)

[//]: # ()
[//]: # (```bibtex)

[//]: # (@article{test_refactoring_impact,)

[//]: # (  title={Understanding Refactoring in Test Code: An Empirical Study},)

[//]: # (  author={[Authors]},)

[//]: # (  journal={[Journal]},)

[//]: # (  year={[Year]})

[//]: # (})

[//]: # (```)

[//]: # (## License)

[//]: # ()
[//]: # (This project is open source. Please refer to individual components for specific licensing terms.)

[//]: # ()
[//]: # (## Contact)

[//]: # ()
[//]: # (For questions about this replication package, please open an issue in this repository.)
