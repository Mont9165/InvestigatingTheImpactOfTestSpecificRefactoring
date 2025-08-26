#!/bin/bash

# Docker entrypoint script for test refactoring research project
set -e

echo "======================================"
echo "Test Refactoring Research Environment"
echo "======================================"

# Create necessary directories if they don't exist
mkdir -p \
    data \
    results \
    1_collect_test_refactoring_commits/src/main/resources/output \
    2_sampling_test_refactor_commits/result \
    3_merge_each_annotator_data_from_refactorhub/result \
    4_manual_inspection/result \
    5_analyze_test_refactoring/src/results \
    5_analyze_test_refactoring/src/smells_result

# Set proper permissions
chmod +x sh_scripts/*.sh 2>/dev/null || true
chmod +x 5_analyze_test_refactoring/sh/*.sh 2>/dev/null || true

echo "Environment setup complete!"
echo ""
echo "Available commands:"
echo "  Phase 1: cd 1_collect_test_refactoring_commits && mkdir temp_jar && cd temp_jar && jar -xf ../GetCommitInformation-1.0-SNAPSHOT.jar && java -cp . get_refactor_commit.GetTestRefactorCommit"
echo "  Phase 2: cd 2_sampling_test_refactor_commits/src && python sampling_only_modified_test_files_commits.py"
echo "  Phase 3: cd 3_merge_each_annotator_data_from_refactorhub/src && python get_annotation_data_from_server.py"
echo "  Phase 4: cd 4_manual_inspection/src && python get_refactoring_data_from_server.py"
echo "  Phase 5: cd 5_analyze_test_refactoring/src/analysis && python rq1/analyze_relationship_general_vs_test.py"
echo "  Test Smells: cd 5_analyze_test_refactoring && ./sh/testsmell.sh"
echo ""
echo "For help, see README.md or run 'ls -la' to explore the project structure."
echo ""

# Execute the command passed to docker run
exec "$@"