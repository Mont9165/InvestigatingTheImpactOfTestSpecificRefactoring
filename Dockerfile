# Multi-stage build for efficient Docker image
FROM python:3.11-slim AS base

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
        wget \
        curl \
        git \
        gcc \
        g++ \
        make \
        bash \
        ca-certificates \
        && rm -rf /var/lib/apt/lists/*

# Install OpenJDK 17 directly from binary distribution (multi-architecture support)
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "amd64" ]; then \
        JAVA_ARCH="x64"; \
    elif [ "$ARCH" = "arm64" ]; then \
        JAVA_ARCH="aarch64"; \
    else \
        echo "Unsupported architecture: $ARCH" && exit 1; \
    fi && \
    wget https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.12%2B7/OpenJDK17U-jdk_${JAVA_ARCH}_linux_hotspot_17.0.12_7.tar.gz && \
    tar -xzf OpenJDK17U-jdk_${JAVA_ARCH}_linux_hotspot_17.0.12_7.tar.gz -C /opt && \
    rm OpenJDK17U-jdk_${JAVA_ARCH}_linux_hotspot_17.0.12_7.tar.gz && \
    ln -s /opt/jdk-17.0.12+7 /opt/java

# Install Maven
RUN wget https://archive.apache.org/dist/maven/maven-3/3.9.9/binaries/apache-maven-3.9.9-bin.tar.gz && \
    tar -xzf apache-maven-3.9.9-bin.tar.gz -C /opt && \
    rm apache-maven-3.9.9-bin.tar.gz && \
    ln -s /opt/apache-maven-3.9.9 /opt/maven

# Set Java and Maven environment variables
ENV JAVA_HOME=/opt/java
ENV MAVEN_HOME=/opt/maven
ENV PATH=$PATH:$JAVA_HOME/bin:$MAVEN_HOME/bin

# Set the working directory
WORKDIR /app

# Copy and install Python requirements first (for better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Build stage for Java components
FROM base AS builder

# Copy Java project files including source code and resources
COPY 1_collect_test_refactoring_commits/pom.xml ./1_collect_test_refactoring_commits/
COPY 1_collect_test_refactoring_commits/src ./1_collect_test_refactoring_commits/src/

# Build Java application
WORKDIR /app/1_collect_test_refactoring_commits
RUN mvn clean compile package -DskipTests

# Copy TestSmellDetector
WORKDIR /app
COPY 5_analyze_test_refactoring/TestSmellDetector ./5_analyze_test_refactoring/TestSmellDetector/

# Final stage
FROM base AS final

# Copy built Java artifacts and source resources from builder stage
COPY --from=builder /app/1_collect_test_refactoring_commits/target/*.jar ./1_collect_test_refactoring_commits/
COPY --from=builder /app/1_collect_test_refactoring_commits/src ./1_collect_test_refactoring_commits/src/
COPY --from=builder /app/5_analyze_test_refactoring/TestSmellDetector ./5_analyze_test_refactoring/TestSmellDetector/

# Copy all source code and scripts
COPY 2_sampling_test_refactor_commits ./2_sampling_test_refactor_commits/
COPY 3_merge_each_annotator_data_from_refactorhub ./3_merge_each_annotator_data_from_refactorhub/
COPY 4_manual_inspection ./4_manual_inspection/
COPY 5_analyze_test_refactoring/src ./5_analyze_test_refactoring/src/
COPY 5_analyze_test_refactoring/sh ./5_analyze_test_refactoring/sh/
COPY sh_scripts ./sh_scripts/

# Make shell scripts executable
RUN find . -name "*.sh" -type f -exec chmod +x {} \;

# Create necessary directories
RUN mkdir -p \
    1_collect_test_refactoring_commits/repos \
    2_sampling_test_refactor_commits/result \
    3_merge_each_annotator_data_from_refactorhub/result \
    4_manual_inspection/result \
    5_analyze_test_refactoring/src/results \
    5_analyze_test_refactoring/src/smells_result

# Copy and set up entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Set environment variables for the research project
ENV PYTHONPATH=/app
ENV RESEARCH_HOME=/app

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Default command
CMD ["/bin/bash"]

# Add labels for documentation
LABEL maintainer="Test Refactoring Research Team"
LABEL description="Docker image for analyzing the impact of test-specific refactoring"
LABEL version="1.0"
