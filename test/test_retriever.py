import asyncio
import os
from src.pattern_workflow import build_github_retriever
from dotenv import load_dotenv

async def test_github_retriever():
    """Test the GitHub retriever functionality."""
    load_dotenv()
    
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable is not set")
        return
        
    try:
        # Build the retriever
        retriever = await build_github_retriever(
            github_token=github_token,
            owner="microservices-patterns",
            repo="ftgo-application",
            branch="master"
        )
        
        if retriever:
            print("Successfully built GitHub retriever!")
            
            # Test a query
            print("\nTesting retriever with a sample query about Saga pattern...")
            nodes = retriever.retrieve("Show me examples of Saga pattern implementation")
            
            print(f"\nFound {len(nodes)} relevant documents")
            for i, node in enumerate(nodes, 1):
                print(f"\nDocument {i}:")
                print(f"Source: {node.metadata.get('file_name', 'Unknown')}")
                print("Content preview:", node.text[:200] + "..." if len(node.text) > 200 else node.text)
                
    except Exception as e:
        print(f"Error during test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Running GitHub retriever test...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(test_github_retriever())
    finally:
        loop.close()