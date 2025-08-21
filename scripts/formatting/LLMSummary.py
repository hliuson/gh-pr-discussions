
import json
import hashlib
import openai
import os
from typing import List, Dict
import time
from dotenv import load_dotenv

load_dotenv()

client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def getComments(input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        comment_list = []
        transformed_data = []
        index = 1
        for item in data:
            comments = item.get("filtered_comments", "")
            combined_comments = '\n'.join(comments)
            print(f"processing comments group #{index}")
            summarized= summarize_comments(combined_comments)
            
            
            transformed_item = {
                "index": index,
                "unsumarized_length": len(combined_comments),
                "unsumarized_comments": combined_comments,
                "sumarized_length": len(summarized),
                "summarized_comments": summarized,
            }
            transformed_data.append(transformed_item)
            comment_list.append(combined_comments)
            index += 1
            time.sleep(1)

        with open(output_file, 'w', encoding="utf-8") as f:
            json.dump(transformed_data, f, indent=2, ensure_ascii=False)

        print(f"Successfully transformed {len(comment_list)}")
        print(f"Output written to: {output_file}")


    except FileNotFoundError:
        print(f"Error: Input file {input_file} not found.")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file '{input_file}")
    except Exception as e:
        print(f"Error: {str(e)}")

def summarize_comments(comments):
    """Send multiple comments in one API call"""

    full_prompt = f"Summarize this PR comment as a brief, natural critique (60-80 words). Write as if you're an experienced developer giving direct feedback. Focus on the core technical points and any decisions made. Avoid verbose explanations and get straight to the point:\n {comments}"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system", 
                "content": "You are an expert code reviewer writing concise, natural critiques. Write brief, flowing summaries that sound like experienced developer feedback. Be direct and technical. Avoid verbose explanations, filler words, and overly formal language. Keep responses under 100 words while maintaining technical accuracy. Use simple transitions like \"however,\" \"but,\" \"while\" sparingly."
            },
            {
                "role": "user", 
                "content": full_prompt
            }
        ],
        max_tokens=250
    )

    # print(full_prompt)
    #print(f"\n\n\n{response.choices[0].message.content}")
    return response.choices[0].message.content

getComments("../../data/filtered/filtered_critique_data.json", "../../data/model-training/summarized_comments.json")