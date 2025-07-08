
"""
Extract Summary Script

This script clones a GitHub repository, lists its microservice folders, 
and asks the OpenAI ChatCompletion API to generate
a brief description and user stories for the pplication.

Dependencies:
    pip install GitPython openai

Environment Variables:
    OPENAI_API_KEY: Your OpenAI API key

Usage:
    python bookinfo_summary.py https://github.com/istio/istio.git
"""

import os
import sys
import tempfile
from git import Repo, GitCommandError
import openai


from dotenv import load_dotenv

load_dotenv()

def clone_repository(repo_url, destination):
    """
    Clone the given repository URL into the destination folder.
    Returns the path to the cloned repository.
    """
    try:
        print(f"Cloning repository {repo_url} into {destination}...")
        Repo.clone_from(repo_url, destination)
        return destination
    except GitCommandError as e:
        print(f"Error cloning repository: {e}", file=sys.stderr)
        sys.exit(1)

def list_microservices(bookinfo_path):
    """
    List subdirectories (microservice folders) under samples/bookinfo.
    """
    try:
        entries = os.listdir(bookinfo_path)
    except FileNotFoundError:
        print(f"Directory not found: {bookinfo_path}", file=sys.stderr)
        sys.exit(1)

    services = [name for name in entries
                if os.path.isdir(os.path.join(bookinfo_path, name))]
    if not services:
        print("No microservice folders found in samples/bookinfo.", file=sys.stderr)
        sys.exit(1)
    return services

def build_prompt(services):
    """
    Build a prompt string listing the microservices and requesting
    a description and user stories.
    """
    service_list = "\n".join(f"- {svc}" for svc in services)
    prompt = (
        "We have a microservices application called Bookinfo. "
        "The Bookinfo directory contains the following services:\n"
        f"{service_list}\n\n"
        "Please provide:\n"
        "1. A brief description of the Bookinfo application.\n"
        "2. A list of associated user stories, numbered."
    )
    return prompt

def get_openai_response(prompt):
    """
    Call OpenAI's ChatCompletion API with the given prompt and return the assistant's reply.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Environment variable OPENAI_API_KEY is not set.", file=sys.stderr)
        sys.exit(1)

    openai.api_key = api_key

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except openai.error.OpenAIError as e:
        print(f"OpenAI API error: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: python bookinfo_summary.py <git_repo_url>", file=sys.stderr)
        sys.exit(1)

    repo_url = sys.argv[1]

    # Create a temporary directory for cloning
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_path = clone_repository(repo_url, tmp_dir)
        bookinfo_dir = os.path.join(repo_path, "samples", "bookinfo")

        print("Listing microservice folders in samples/bookinfo...")
        services = list_microservices(bookinfo_dir)
        print(f"Found services: {', '.join(services)}")

        # Build and send the prompt to OpenAI
        prompt = build_prompt(services)
        print("\nSending prompt to OpenAI...")
        ai_output = get_openai_response(prompt)

        # Print the AI-generated description and user stories
        print("\n=== AI Response ===")
        print(ai_output)

if __name__ == "__main__":
    main()

