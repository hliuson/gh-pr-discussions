# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a machine learning project focused on analyzing GitHub PR discussions and comments. The project uses Python for data processing, machine learning model training, and text analysis of GitHub pull request data.

## Architecture

The project is structured as a data pipeline with machine learning components:

### Core Components
- **Data Pipeline** (`scripts/pipeline/`): Multi-stage data processing pipeline that discovers repositories, extracts PR data, filters content, and prepares training data
- **Machine Learning Models** (`models/`): Contains trained models including a sentence transformer model for text analysis and a classifier for comment categorization
- **Data Processing** (`scripts/formatting/`): Scripts for transforming and formatting data from GitHub APIs
- **Training Scripts** (`scripts/sentence-transformer/`, `scripts/critique-model/`): Model training and fine-tuning scripts

### Key Directories
- `data/`: Contains pipeline outputs, training data, and processed datasets organized by processing stage
- `models/`: Stores trained models including sentence transformers and classifiers
- `scripts/`: All Python scripts organized by functionality (pipeline, formatting, training)

## Development Environment

### Dependencies
The project uses uv for dependency management. Install dependencies with:
```bash
cd scripts
uv sync
```

Key dependencies include:
- `sentence-transformers>=5.1.0` for text embedding models
- `scikit-learn>=1.7.1` for machine learning
- `pandas>=2.3.1` for data processing
- `requests>=2.32.4` for API calls
- `openai>=1.100.2` for AI model integration
- `aiohttp>=3.12.15` for async HTTP requests

### Python Environment
- Requires Python >=3.12
- Uses asyncio for concurrent data processing
- Leverages GPU acceleration when available for model training

## Data Pipeline Architecture

The pipeline processes GitHub data through multiple stages:

1. **Repository Discovery** (`discover_repo.py`): Identifies quality repositories (~2000 repos total)
2. **PR Extraction** (`extract_prs.py`): Extracts pull request data and comments
3. **Data Filtering** (`ST_filter_data.py`): Applies quality filters using sentence transformers
4. **Comment Processing** (`summarize_comments.py`): Processes and summarizes PR comments *(runs in parallel with step 5)*
5. **Code Diff Analysis** (`filter_codediff.py`): Analyzes code changes *(runs in parallel with step 4)*
6. **Data Transformation** (`transform_critique_data.py`): Combines outputs from steps 4 & 5

### Pipeline Parallelization Strategy

**Sequential Dependencies:**
Steps 1 → 2 → 3 must run in sequence due to data dependencies.

**Parallel Execution Optimization:**
Steps 4 and 5 can run simultaneously after step 3 completes:
- Both process the same filtered input data from `ST_filter_data.py`
- No interdependencies between comment summarization and code diff filtering
- **Performance Gain**: ~40-50% reduction in pipeline execution time

**Implementation:**
```python
# Parallel execution using asyncio.gather()
filtered_data = await ST_filter_data()  # Step 3
summarized, code_filtered = await asyncio.gather(
    summarize_comments(filtered_data),  # Step 4: OpenAI API calls
    filter_codediff(filtered_data)      # Step 5: CPU regex processing
)
final_data = transform_critique_data(summarized, code_filtered)  # Step 6
```

**Resource Utilization:**
- **CPU**: Maximized during regex processing (step 5)
- **Network**: API calls to OpenAI (step 4) 
- **GPU**: Available for sentence transformer inference (step 3)
- **Memory**: Shared read-only access to filtered data

### Scaled Production Pipeline (RunPod)

The pipeline is designed for large-scale automated data collection with these specifications:

**Current Production Parameters:**
- 40 repositories per iteration
- 60 PRs searched per repository (filtered to quality PRs only)
- Target: 2,400 PRs per hour iteration
- Total goal: 120,000 PRs searched across 50 hours
- Will cycle through all 2,000 repositories exactly once
- **Parallel processing**: Steps 4&5 reduce iteration time from ~55min to ~45min

**GitHub API Constraints:**
- Search API: 30 requests/minute (pipeline uses 2.5s delays)
- REST API: 5,000 requests/hour (comments + diffs = 2 calls per PR)
- Pipeline makes ~4,800 API calls per hour (within limits)

**Concurrency Settings:**
- `asyncio.Semaphore(60-80)` recommended for RunPod deployment
- Current semaphore value can be increased from 10 for production

### Pipeline Execution
Run the full pipeline with:
```bash
cd scripts/pipeline
python fullpipeline.py
```

## Model Training

### Sentence Transformer Training
The project includes scripts for training sentence transformer models for comment classification:
```bash
cd scripts/sentence-transformer
python train_classifier.py
```

### Critique Model Training
For training critique/feedback models:
```bash
cd scripts/critique-model
python SFT_trainer.py
```

## Data Processing

The project processes GitHub PR data through several transformations:
- Comment labeling and formatting for training data
- Repository metadata transformation
- PR discussion analysis and filtering

## Model Artifacts

The trained models are stored in `models/`:
- `sentence_transformer_model/`: Fine-tuned sentence transformer for text analysis
- `best_classifier.pkl`: Trained classifier for comment categorization
- `model_info.json`: Metadata about trained models

## Critical Implementation Questions for Production Deployment

For the scaled RunPod deployment, these architectural decisions need to be addressed:

1. **Repo State Tracking**: How to track which 40 repos to process in each iteration? 
   - Modify `getRepos()` to accept offset/batch parameters?
   - Add iteration logic to slice `repos[iteration*40:(iteration+1)*40]`?

2. **Progress Persistence**: How to handle crash recovery?
   - Save iteration state to file for resuming from correct repo set
   - Prevent starting over from repos 0-39 after crashes

3. **Data Aggregation Strategy**: How to handle output from 50 iterations?
   - **DECIDED**: Create separate critique_data files per iteration (`critique_data_iter0.json` through `critique_data_iter49.json`)
   - Combine final critique_data JSONs after all 50 iterations complete
   - **Rationale**: critique_data is the final training-ready product, much smaller than intermediate pr_cleaned data
   - Provides crash safety, quality validation per iteration, and efficient final merge

4. **Iteration Control**: What triggers hourly cycles?
   - **DECIDED**: Internal script loop with `time.sleep(3600)` between iterations
   - Single long-running container with integrated state management
   - Natural stopping after 50 iterations without external scheduling

5. **Stopping Logic**: Track both conditions (50 hours AND 120k PRs searched) or stop on first completion?
   - **DECIDED**: Simple iteration counter - stop after exactly 50 iterations
   - Ignore PR count and time elapsed for clean termination logic

6. **Error Handling**: Retry logic for failed repos/PRs and handling of GitHub API errors during long runs
   - **DECIDED**: Multi-level retry architecture with comprehensive error logging
   
   **API-Level Retry Logic:**
   - 3 retry attempts with exponential backoff (1s, 2s, 4s)
   - Handle specific HTTP codes: 429 (rate limit), 502/503 (server errors), timeouts
   - Log each retry attempt with error details
   
   **Repo-Level Error Handling:**
   - If all API retries for a repo fail → skip repo, log error, continue
   - Update checkpoint with failed repo list
   - Don't halt entire iteration for single repo failure
   
   **Iteration-Level Retry:**
   - Failed iterations: Halt pipeline, retry entire iteration once after 1 hour
   - If second attempt fails → skip iteration, log, continue to next
   - Track iteration success/failure rates
   
   **Structured Error Logging:**
   - `error_log_iter{N}.json` per iteration with structured failure data
   - Aggregate `pipeline_errors.json` for full run analysis
   - Track: timestamp, error_type, repo_id, api_endpoint, http_status, retry_count, final_action

## Progress Persistence & Recovery Strategy

The 50-hour automated pipeline requires robust crash recovery mechanisms optimized for RunPod's auto-restart capabilities.

### Multi-Level Persistence Approach

| Persistence Level | Granularity | Resume Trigger | Resume Point | Data Loss |
|------------------|-------------|----------------|--------------|-----------|
| **Iteration-Level** | Per 40 repos | Next hour cycle | Start of current iteration | ~35 minutes work |
| **Repo-Level** | Per repo | Immediate restart | Continue from next repo | ~2-5 minutes work |
| **API-Level** | Per API call | Immediate retry | Retry failed call | None |

### RunPod Auto-Restart Recovery Timeline

| Scenario | Detection Time | Restart Time | Resume Time | Total Downtime | Data Loss |
|----------|----------------|--------------|-------------|----------------|-----------|
| **Manual Restart** | 5-60 minutes | 1-5 minutes | Immediate | 6-65 minutes | 1 repo worth |
| **RunPod Auto-Restart** | 10-30 seconds | 30-60 seconds | Immediate | 1-2 minutes | 1 repo worth |

### Recommended Strategy: Repo-Level Persistence
- **Checkpoint frequency**: Save after each repo completes (40 saves per iteration)
- **Storage**: RunPod persistent volume for checkpoint files
- **Cleanup**: Remove checkpoints after successful iteration completion
- **Resume logic**: Load checkpoint on startup, continue from last completed repo

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.