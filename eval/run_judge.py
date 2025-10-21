import pandas as pd
import asyncio
import json

from benchmark.judge import DalleJudge
from llama_index.core.workflow import StartEvent
from gen import get_retrievers  # Assumed to exist as per the code

# Load input Excel
df = pd.read_excel("/Users/marcocalamo/DALLE/results_open.xlsx")

# Initialize judge and retriever
judge = DalleJudge(timeout=None)
retriever = get_retrievers()

async def run_all():
    results = []

    for _, row in df.iterrows():
        try:
            microservices = row["Dalle Output"]
            specs = row["System Description"]
            user_stories = row["User Stories"]


            result = await judge.run(retriever=retriever, specs=specs, user_stories=user_stories, microservices_list=microservices)
            parsed = json.loads(result)

            results.append({
                "specs": specs,
                "user_stories": user_stories,
                "microservices_list": microservices,
                "judgment": parsed
            })

        except Exception as e:
            raise e
            results.append({
                "specs": row.get("specs", ""),
                "user_stories": row.get("user_stories", ""),
                "microservices_list": row.get("microservices_list", ""),
                "error": str(e)
            })

    pd.DataFrame(results).to_excel("judged_outputs_open.xlsx", index=False)
    print("Saved to judged_outputs.xlsx")

if __name__ == "__main__":
    asyncio.run(run_all())
