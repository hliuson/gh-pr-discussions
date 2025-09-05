
import json
import hashlib
import openai
import asyncio
from openai import AsyncOpenAI
import os
from typing import List, Dict
import time
from dotenv import load_dotenv

load_dotenv()

client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
async_client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))

async def getComments(input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        transformed_data = await process_concurrently(data)

        with open(output_file, 'w', encoding="utf-8") as f:
            json.dump(transformed_data, f, indent=2, ensure_ascii=False)

        print(f"Successfully transformed {len(transformed_data)}")
        print(f"Output written to: {output_file}")


    except FileNotFoundError:
        print(f"Error: Input file {input_file} not found.")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file '{input_file}")
    except Exception as e:
        print(f"Error: {str(e)}")

async def summarize_comments(comments):
    """Send multiple comments in one API call"""

    # User Prompt v1: Summarize this PR comment as a brief, natural critique (60-80 words). Write as if you're an experienced developer giving direct feedback. Focus on the core technical points and any decisions made. Avoid verbose explanations and get straight to the point:\n {comments}   
    # System Prompt v1 : You are an expert code reviewer writing concise, natural critiques. Write brief, flowing summaries that sound like experienced developer feedback. Be direct and technical. Avoid verbose explanations, filler words, and overly formal language. Keep responses under 100 words while maintaining technical accuracy. Use simple transitions like \"however,\" \"but,\" \"while\" sparingly.

    # User Prompt v2: Summarize this PR comment preserving key technical details and specific concerns (120-150 words). Focus on: concrete technical issues raised, specific implementation suggestions, security or architectural concerns, and any decisions made. Preserve technical terminology and actionable feedback:\n {comments}
    # System Prompt v2: You are an expert code reviewer writing technical summaries. Preserve specific concerns, implementation details, and technical terminology. Focus on actionable feedback rather than high-level themes. Include concrete technical points like API designs, security considerations, or architectural decisions. Be direct but maintain technical accuracy.     

    full_prompt = f"Summarize this PR comment preserving key technical details and specific concerns (120-150 words). Focus on: concrete technical issues raised, specific implementation suggestions, security or architectural concerns, and any decisions made. Preserve technical terminology and actionable feedback:\n {comments}"

    response = await async_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system", 
                "content": "You are an expert code reviewer writing technical summaries. Preserve specific concerns, implementation details, and technical terminology. Focus on actionable feedback rather than high-level themes. Include concrete technical points like API designs, security considerations, or architectural decisions. Be direct but maintain technical accuracy."
            },
            {
                "role": "user", 
                "content": full_prompt
            }
        ],
        max_tokens=325
    )

    # print(full_prompt)
    #print(f"\n\n\n{response.choices[0].message.content}")
    return response.choices[0].message.content

async def process_concurrently(data, semaphore_limit=5):
    semaphore = asyncio.Semaphore(semaphore_limit)

    async def process_item(item, index):
        async with semaphore:
            comments = '\n'.join(item.get("filtered_comments", ""))
            print(f"processing comment #{index}")
            summarized = await summarize_comments(comments)
            return {
                "index": index,
                "unsumarized_length": len(comments),
                "unsumarized_comments": comments,
                "sumarized_length": len(summarized),
                "summarized_comments": summarized,
            }
    
    tasks = [process_item(item, i+1) for i, item in enumerate(data)]
    return await asyncio.gather(*tasks)
  
asyncio.run(getComments("../../data/pipeline/4_filtered_data.json", "../../data/pipeline/5_summarized_comments1.json"))   