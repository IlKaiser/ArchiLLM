import os
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import List
from urllib.parse import urlparse

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding


# Load dot evironment variables
from dotenv import load_dotenv
load_dotenv()

class GitHubRepoAnalyzer:
    def __init__(self, openai_api_key: str):
        """Initialize the analyzer with OpenAI API key."""
        # Configure LlamaIndex settings
        Settings.llm = OpenAI(model="gpt-4o-mini", api_key=openai_api_key)
        Settings.embed_model = OpenAIEmbedding(api_key=openai_api_key)
        
        self.temp_base_dir = tempfile.mkdtemp(prefix="github_repos_")
        print(f"Working in temporary directory: {self.temp_base_dir}")
    
    def read_repo_links(self, file_path: str) -> List[str]:
        """Read GitHub repository links from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                links = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            return links
        except FileNotFoundError:
            print(f"Error: File {file_path} not found.")
            return []
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return []
    
    def extract_repo_name(self, github_url: str) -> str:
        """Extract repository name from GitHub URL."""
        parsed = urlparse(github_url)
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) >= 2:
            return f"{path_parts[0]}_{path_parts[1]}"
        return "unknown_repo"
    
    def clone_repository(self, repo_url: str, dest_dir: str) -> bool:
        """Clone a GitHub repository to the specified directory."""
        try:
            # Create destination directory
            os.makedirs(dest_dir, exist_ok=True)
            
            # Clone the repository
            result = subprocess.run(
                ['git', 'clone', repo_url, dest_dir],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                print(f"Successfully cloned {repo_url}")
                return True
            else:
                print(f"Failed to clone {repo_url}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"Timeout while cloning {repo_url}")
            return False
        except Exception as e:
            print(f"Error cloning {repo_url}: {e}")
            return False
    
    def load_and_index_repository(self, repo_path: str) -> VectorStoreIndex:
        """Load repository files and create a vector index."""
        try:
            # Define file extensions to include
            required_exts = ['.py', '.js', '.ts', '.java', '.go', '.rs', '.cpp', '.c', '.h', 
                           '.md', '.txt', '.yml', '.yaml', '.json', '.xml', '.dockerfile', 
                           '.sh', '.bat', '.sql', '.html', '.css', '.vue', '.jsx', '.tsx']
            
            # Load documents from the repository
            reader = SimpleDirectoryReader(
                input_dir=repo_path,
                required_exts=required_exts,
                recursive=True,
                exclude_hidden=True
            )
            
            documents = reader.load_data()
            
            if not documents:
                print(f"No documents found in {repo_path}")
                return None
            
            # Create vector index
            index = VectorStoreIndex.from_documents(documents)
            print(f"Indexed {len(documents)} documents from repository")
            return index
            
        except Exception as e:
            print(f"Error indexing repository {repo_path}: {e}")
            return None
    
    
    def generate_system_description(self, index: VectorStoreIndex, repo_name: str) -> str:
        """Generate system description and user stories using the indexed repository."""
        try:
            # Create query engine
            query_engine = index.as_query_engine()
            
            # Query for system description
            system_query = """
            Analyze this microservice application repository and provide:
            1. A brief description of the system - what it does, its main purpose, and key technologies used
            2. A comprehensive list of user stories that describe the functionality from an end-user perspective
            
            Format your response as:
            SYSTEM DESCRIPTION:
            [Brief description of the system]
            
            USER STORIES:
            [List of user stories in the format: "As a [user type], I want to [action] so that [benefit]"]
            """
            
            response = query_engine.query(system_query)
            return str(response)
            
        except Exception as e:
            print(f"Error generating description for {repo_name}: {e}")
            return f"Error: Could not generate description for {repo_name}"
    
    def format_output(self, raw_response: str) -> str:
        """Format the raw response into the required format."""
        try:
            lines = raw_response.split('\n')
            formatted_lines = []
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if 'SYSTEM DESCRIPTION' in line.upper():
                    current_section = 'description'
                    formatted_lines.append('# SYSTEM DESCRIPTION')
                    continue
                elif 'USER STORIES' in line.upper():
                    current_section = 'stories'
                    formatted_lines.append('\n# USER STORIES')
                    continue
                
                if current_section == 'description' and line and not line.startswith('#'):
                    formatted_lines.append(line)
                elif current_section == 'stories' and line and not line.startswith('#'):
                    if not line.startswith('- ') and not line.startswith('* '):
                        formatted_lines.append(f"- {line}")
                    else:
                        formatted_lines.append(line)
            
            return '\n'.join(formatted_lines)
            
        except Exception as e:
            print(f"Error formatting output: {e}")
            return raw_response
    
    def save_input_file(self, content: str, repo_name: str, output_dir: str = "output"):
        """Save the generated content to input.txt file."""
        try:
            # Create output directory structure
            repo_output_dir = Path(output_dir) / repo_name
            repo_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save to input.txt
            input_file_path = repo_output_dir / "input.txt"
            with open(input_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Saved input.txt for {repo_name} to {input_file_path}")
            
        except Exception as e:
            print(f"Error saving input file for {repo_name}: {e}")
    
    def process_repositories(self, repo_links_file: str, output_dir: str = "output"):
        """Main method to process all repositories."""
        try:
            # Read repository links
            repo_links = self.read_repo_links(repo_links_file)
            if not repo_links:
                print("No repository links found.")
                return
            
            print(f"Found {len(repo_links)} repositories to process")
            
            # Process each repository
            for i, repo_url in enumerate(repo_links, 1):
                print(f"\n--- Processing repository {i}/{len(repo_links)}: {repo_url} ---")
                
                # Extract repository name
                repo_name = self.extract_repo_name(repo_url)
                print(f"Repository name: {repo_name}")
                
                # Clone repository
                clone_dir = os.path.join(self.temp_base_dir, repo_name)
                if not self.clone_repository(repo_url, clone_dir):
                    print(f"Skipping {repo_name} due to clone failure")
                    continue
                
                # Index repository
                index = self.load_and_index_repository(clone_dir)
                if index is None:
                    print(f"Skipping {repo_name} due to indexing failure")
                    continue
                
                # Generate description and user stories
                raw_response = self.generate_system_description(index, repo_name)
                formatted_content = self.format_output(raw_response)
                
                # Save to file
                self.save_input_file(formatted_content, repo_name, output_dir)
                
                print(f"Completed processing {repo_name}")
            
            print(f"\n✅ Processing complete! Output files saved in '{output_dir}' directory")
            
        except Exception as e:
            print(f"Error in process_repositories: {e}")
        finally:
            # Clean up temporary directory
            self.cleanup()
    
    def cleanup(self):
        """Clean up temporary directories."""
        try:
            if os.path.exists(self.temp_base_dir):
                shutil.rmtree(self.temp_base_dir)
                print(f"Cleaned up temporary directory: {self.temp_base_dir}")
        except Exception as e:
            print(f"Error during cleanup: {e}")


def main():
    """Main function to run the GitHub repository analyzer."""
    # Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    REPO_LINKS_FILE = 'github_repos.txt'
    OUTPUT_DIR = 'output'
    
    if not OPENAI_API_KEY:
        print("Error: Please set the OPENAI_API_KEY environment variable")
        return
    
    # Create analyzer instance
    analyzer = GitHubRepoAnalyzer(OPENAI_API_KEY)
    
    # Process repositories
    analyzer.process_repositories(REPO_LINKS_FILE, OUTPUT_DIR)


if __name__ == "__main__":
    main()