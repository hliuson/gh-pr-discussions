import shutil
import os
from pathlib import Path

def download_filtered_critique_data():
    file = "6_filtered_codediff.json"
    
    # Source file path (relative to project root)
    source_file = Path(f"../../data/pipeline/{file}")
    
    # Get user's Downloads folder
    downloads_folder = Path.home() / "Downloads"
    
    # Destination file path
    destination_file = downloads_folder / file
    
    try:
        # Check if source file exists
        if not source_file.exists():
            print(f"Error: Source file {source_file} does not exist")
            return False
        
        # Copy the file
        shutil.copy2(source_file, destination_file)
        print(f"Successfully downloaded {source_file} to {destination_file}")
        print(f"File size: {destination_file.stat().st_size:,} bytes")
        
        return True
        
    except Exception as e:
        print(f"Error downloading file: {e}")
        return False

download_filtered_critique_data()