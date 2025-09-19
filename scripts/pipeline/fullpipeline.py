import asyncio
import json
import os
from datetime import datetime

from extract_prs import prDiscussionExtraction
from ST_filter_data import filter_comments as st_filter
from summarize_comments import process_comments_concurrently as summarize
from filter_codediff import getCodeDiff
from transform_critique_data import get_model_data as transform_critique

from shared_utils import TEST_MODE, log_error
import random

input_file = '../../data/pipeline/1_quality_repos.json'
checkpoint_dir = "../../data/checkpoints"
os.makedirs(checkpoint_dir, exist_ok=True)
iterations_dir =  "../../data/iterations"
critique_dir = f"{iterations_dir}/critique"
os.makedirs(critique_dir, exist_ok=True)

def load_repo_batch(iteration, batch_size=40):

    with open(input_file, 'r', encoding='utf-8') as f:
        all_repos = json.load(f)
    
    start_index = iteration * batch_size
    end_index = start_index + batch_size

    repo_batch = all_repos[start_index:end_index]

    print(f"Iteration {iteration}: Loading repos {start_index}-{end_index-1} ({len(repo_batch)}) repos")

    return repo_batch

def save_checkpoint(iteration, completed_repos, last_completed_repo, total_repos=40, status="in_progress"):

    if TEST_MODE and random.random() < 0.1:
          raise IOError("Simulated disk space error")

    checkpoint_data = {
      "iteration": iteration,
      "completed_repos": completed_repos,
      "total_repos": total_repos,
      "last_completed_repo": last_completed_repo,
      "start_time": datetime.now().isoformat(),
      "status": status 
    }

    checkpoint_file = f'{checkpoint_dir}/checkpoint_iter{iteration}.json'

    try:
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, indent=2)

    except Exception as e:
        print(f"Warning: Failed to save checkpoint - {e}")
    

def load_checkpoint(iteration):
    checkpoint_file = f'{checkpoint_dir}/checkpoint_iter{iteration}.json'

    try:
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)
        return checkpoint
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Warning: Unable to load checkpoint - {e}")
        return None
    
def cleanup_checkpoint(iteration):
    checkpoint_file = f'{checkpoint_dir}/checkpoint_iter{iteration}.json'
    try:
        os.remove(checkpoint_file)
        print(f"Checkpoint cleaned up: iteration {iteration}")
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"Warning: Failed to cleanup checkpoint - {e}")

def get_resume_point():
    latest_completed = -1

    for iteration in range(49, -1, -1):
        checkpoint = load_checkpoint(iteration)
        if checkpoint:
            if checkpoint['status'] == 'completed':
                latest_completed = max(latest_completed, iteration)
                continue
            else:
                return iteration, checkpoint['completed_repos']
    return latest_completed + 1, 0

async def run_iteration(iteration, start_repo):


    # Step 1: PR Discussion Extraction
    print(f"\n=== STARTING ITERATION {iteration} ===")
    repo_batch = load_repo_batch(iteration)
    try:
        discussions = await prDiscussionExtraction(
            repo_batch,
            iteration,
            checkpoint_callback=save_checkpoint,
            start_repo=start_repo
        )
    except Exception as e:
        log_error("pipeline_failure", "prDiscussionExtraction", {
            "iteration": iteration,
            "error": str(e)
        }, iteration)
        raise
    # Step 2: Filter with sentence transformer
    print(f"\n=== FILTERING DATA ===")

    try:
        filtered_data  = await st_filter(discussions)
    except Exception as e:
        log_error("pipeline_failure", "st_filter", {
            "iteration": iteration,
            "error": str(e),
            "input_size": len(discussions)
        }, iteration)
        raise

    # Step 3 & 4: Parallel processing
    print(f"PARALLEL PROCESSING")

    try:
        summarized_comments, filtered_codediff = await asyncio.gather(
            summarize(filtered_data, semaphore_limit=5),
            getCodeDiff(filtered_data)
        )
    except Exception as e:
        log_error("pipeline_failure", "parallel processing of comments summary and codediff", {
            "iteration": iteration,
            "error": str(e)
        }, iteration)
        raise

    # Step 5 Transform to critique data
    print(f"\n=== TRANSFORMING CRITIQUE DATA ===")

    try:
        critique_data = await transform_critique(iteration, summarized_comments, filtered_codediff)
    except Exception as e:
        log_error("pipeline_failure", "transform_critique", {
            "iteration": iteration,
            "error": str(e)
        }, iteration)

    output_file =  f'{critique_dir}/critique_data_iter{iteration}.json'

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(critique_data, f, indent=2)
    except Exception as e:
        log_error("io_failure", "save_critique_data", {
            "iteration": iteration,
            "output_file": output_file,
            "error": str(e)
        }, iteration)
        raise

    print(f"Saved {len(critique_data)} critique records to {output_file}")

    print(f"\n === COMPLETED ITERATION {iteration} ===")

    cleanup_checkpoint(iteration)

async def main():

    print("Starting 50 hour automated pipeline...")

    start_iteration, start_repo = get_resume_point()
    print(f"Resuming from iteration {start_iteration}, repo {start_repo}")

    for iteration in range(start_iteration, 3): #TEST change back to 50
        current_start_repo = start_repo if iteration == start_iteration else 0
        try:
          await run_iteration(iteration + 1, current_start_repo)
        except Exception as e:
          print(f"❌ ITERATION {iteration + 1} FAILED: {e}")
          log_error("iteration_failure", "run_iteration", {
              "iteration": iteration + 1,
              "error": str(e)
          }, iteration + 1)
          print(f"⏭️  Continuing to next iteration...")
          continue
        

        if iteration < 49:
            print(f"Sleeping for 1 hour before iteration {iteration + 1}...")
            await asyncio.sleep(10) #TEST change back to 3600

asyncio.run(main())