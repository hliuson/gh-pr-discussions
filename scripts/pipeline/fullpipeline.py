import asyncio
import json
import os
from datetime import datetime

from extract_prs import prDiscussionExtraction

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
    
    print(f"\n=== STARTING ITERATION {iteration} ===")
    repo_batch = load_repo_batch(iteration)

    discussions = await prDiscussionExtraction(
        repo_batch,
        iteration,
        checkpoint_callback=save_checkpoint,
        start_repo=start_repo
    )
    #Filter with sentence transformer
    #Parallel comment summarization + code diff filtering
    #Transform to critique data

    output_file =  f'{critique_dir}critique_data_iter{iteration}.json'

    print(f"\n === COMPLETED ITERATION {iteration} ===")

    #cleanup_checkpoint(iteration)

async def main():

    print("Starting 50 hour automated pipeline...")

    start_iteration, start_repo = get_resume_point()
    print(f"Resuming from iteration {start_iteration}, repo {start_repo}")

    for iteration in range(start_iteration, 3): #TEST change back to 50
        current_start_repo = start_repo if iteration == start_iteration else 0
        await run_iteration(iteration, current_start_repo)

        if iteration < 49:
            print(f"Sleeping for 1 hour before iteration {iteration + 1}...")
            await asyncio.sleep(10) #TEST change back to 3600

asyncio.run(main())