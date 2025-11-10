#!/usr/bin/env python3
"""
Batch processing script for the ArchiLLM dataset.
Iterates over the dataset folder and processes each input.txt file,
extracting SYSTEM DESCRIPTION and USER STORIES, then running the DalleWorkflow.
Results are saved as JSON files with the corresponding folder name.
"""

import asyncio
import json
import re
from pathlib import Path
from typing import Dict, Tuple, Optional
from dotenv import load_dotenv

# Ensure environment is loaded
assert load_dotenv()

# Import the workflow and utilities
from test import DalleWorkflow
from utils import to_dict


def extract_section_from_input(file_path: Path, section_name: str) -> Optional[str]:
    """
    Extract a section from input.txt file.
    
    Args:
        file_path: Path to the input.txt file
        section_name: Name of the section (e.g., "SYSTEM DESCRIPTION", "USER STORIES")
    
    Returns:
        The content of the section, or None if not found
    """
    if not file_path.exists():
        return None
    
    try:
        content = file_path.read_text(encoding="utf-8")
        
        # Find the section
        section_marker = f"# {section_name}:"
        if section_marker not in content:
            return None
        
        # Extract content after the marker
        start_idx = content.find(section_marker) + len(section_marker)
        
        # Find the next section marker or end of file
        remaining_content = content[start_idx:]
        next_section = re.search(r'^# [A-Z ]+:', remaining_content, re.MULTILINE)
        
        if next_section:
            end_idx = start_idx + next_section.start()
            section_content = content[start_idx:end_idx]
        else:
            section_content = remaining_content
        
        # Clean up: strip whitespace and empty lines at start/end
        section_content = section_content.strip()
        
        return section_content if section_content else None
    
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None


def find_input_files(dataset_dir: Path, max_depth: int = 3) -> list[Tuple[Path, str]]:
    """
    Find all input.txt files in the dataset directory up to max_depth.
    
    Args:
        dataset_dir: Path to the dataset directory
        max_depth: Maximum depth to search (default: 3)
    
    Returns:
        List of tuples (input_file_path, folder_name)
    """
    input_files = []
    
    def walk_directory(current_path: Path, current_depth: int = 0):
        if current_depth > max_depth:
            return
        
        try:
            for item in current_path.iterdir():
                if item.is_file() and item.name == "input.txt":
                    # Get the immediate parent folder name
                    folder_name = item.parent.name
                    input_files.append((item, folder_name))
                elif item.is_dir() and current_depth < max_depth:
                    walk_directory(item, current_depth + 1)
        except PermissionError:
            pass
    
    walk_directory(dataset_dir)
    return input_files


async def process_input_file(
    input_file: Path,
    folder_name: str,
    output_dir: Path,
    retriever=None,
    model: str = "openai"
) -> Dict:
    """
    Process a single input.txt file through the DalleWorkflow.
    
    Args:
        input_file: Path to the input.txt file
        folder_name: Name of the folder for output file
        output_dir: Directory where to save the result JSON
        retriever: Optional retriever for the workflow
        model: LLM model to use (default: "openai")
    
    Returns:
        Dictionary with processing results
    """
    result = {
        "folder_name": folder_name,
        "input_file": str(input_file),
        "status": "pending",
        "specs": None,
        "user_stories": None,
        "output": None,
        "error": None
    }
    
    try:
        # Extract sections from input.txt
        specs = extract_section_from_input(input_file, "SYSTEM DESCRIPTION")
        user_stories = extract_section_from_input(input_file, "USER STORIES")
        
        if not specs or not user_stories:
            result["status"] = "skipped"
            result["error"] = "Missing SYSTEM DESCRIPTION or USER STORIES"
            print(f"⚠️  Skipped {folder_name}: Missing required sections")
            return result
        
        result["specs"] = specs
        result["user_stories"] = user_stories
        
        print(f"🔄 Processing {folder_name}...")
        print(f"   Specs length: {len(specs)} chars")
        print(f"   User stories length: {len(user_stories)} chars")
        
        # Run the workflow
        try:
            workflow = DalleWorkflow(timeout=None)
            output = await workflow.run(
                specs=specs,
                user_stories=user_stories,
                retriever=retriever,
                model=model
            )
            
            result["status"] = "success"
            result["output"] = to_dict(output) if output else None
            print(f"✅ Successfully processed {folder_name}")
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = f"Workflow error: {str(e)}"
            print(f"❌ Error processing {folder_name}: {str(e)}")
    
    except Exception as e:
        result["status"] = "error"
        result["error"] = f"Processing error: {str(e)}"
        print(f"❌ Error in {folder_name}: {str(e)}")
    
    # Save result to file
    try:
        output_file = output_dir / f"{folder_name}.json"
        output_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
        result["output_file"] = str(output_file)
    except Exception as e:
        print(f"❌ Error saving output for {folder_name}: {str(e)}")
        result["error"] = f"Save error: {str(e)}"
    
    return result


async def main(
    dataset_dir: Optional[str] = None,
    output_dir: Optional[str] = None,
    max_depth: int = 3,
    model: str = "openai",
    retriever=None
):
    """
    Main batch processing function.
    
    Args:
        dataset_dir: Path to dataset directory (default: ./dataset)
        output_dir: Path where to save results (default: ./results)
        max_depth: Maximum directory depth to search
        model: LLM model to use
        retriever: Optional retriever instance
    """
    # Setup paths
    dataset_path: Path
    if dataset_dir is None:
        dataset_path = Path(__file__).parent.parent / "dataset"
    else:
        dataset_path = Path(dataset_dir)
    
    output_path: Path
    if output_dir is None:
        output_path = Path(__file__).parent.parent / "results"
    else:
        output_path = Path(output_dir)
    
    # Ensure output directory exists
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"🔍 Searching for input.txt files in {dataset_path} (max depth: {max_depth})...")
    
    # Find all input files
    input_files = find_input_files(dataset_path, max_depth=max_depth)
    
    if not input_files:
        print("❌ No input.txt files found")
        return
    
    print(f"📁 Found {len(input_files)} input files to process\n")
    
    # Process each file
    results = []
    for input_file, folder_name in input_files:
        result = await process_input_file(
            input_file,
            folder_name,
            output_path,
            retriever=retriever,
            model=model
        )
        results.append(result)
        print()
    
    # Save summary
    summary = {
        "total_files": len(input_files),
        "successful": sum(1 for r in results if r["status"] == "success"),
        "skipped": sum(1 for r in results if r["status"] == "skipped"),
        "errors": sum(1 for r in results if r["status"] == "error"),
        "results": results
    }
    
    summary_file = output_path / "summary.json"
    summary_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    
    print("\n" + "="*60)
    print("📊 PROCESSING SUMMARY")
    print("="*60)
    print(f"Total files:    {summary['total_files']}")
    print(f"Successful:     {summary['successful']}")
    print(f"Skipped:        {summary['skipped']}")
    print(f"Errors:         {summary['errors']}")
    print(f"Results saved to: {output_path}")
    print("="*60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Batch process ArchiLLM dataset"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Path to dataset directory (default: ./dataset)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output directory (default: ./results)"
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=3,
        help="Maximum directory depth to search (default: 3)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="openai",
        choices=["openai", "anthropic", "mistral"],
        help="LLM model to use (default: openai)"
    )
    
    args = parser.parse_args()
    
    # Run the main function
    asyncio.run(main(
        dataset_dir=args.dataset,
        output_dir=args.output,
        max_depth=args.depth,
        model=args.model
    ))
