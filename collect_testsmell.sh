#!/bin/bash
#SBATCH --job-name=test-smell
#SBATCH --output=logs/job.out
#SBATCH --error=errors/job.err
#SBATCH --time=4-04:00:00
#SBATCH --partition=ocigpu8a100_long
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G


module load singularity
singularity exec collect-test-smell_latest.sif sh /work/kosei-ho/InvestigatingTheImpactOfTestSpecificRefactoring/5_analyze_test_smell/sh/testsmell.sh

