import json

async def get_model_data(iteration, summary_data, codediff_data):

    transformed_data = []
    examine_data = []
    examine_final = []
    final_data = []
    index = 0

    for item in summary_data:
        transformed_item = {
            "index": index,
            "comments": item.get("summarized_comments", ""),
            "codeDiff": None,
            "token_estimation": None
        }
        examine_item = {
            "index": index,
            "codeDiff": None,
            "og_comments": item.get("og_comments", ""),
            "summarized_comments": item.get("summarized_comments", ""),
            "codeDiff_len": None,
            "summary_len": len(item.get("summarized_comments", ""))
        }

        transformed_data.append(transformed_item)
        examine_data.append(examine_item)
    

    for i, item in enumerate(codediff_data):
        transformed_data[i]["codeDiff"] = item.get("diff", "")
        examine_data[i]["codeDiff"] = item.get("diff", "")
        examine_data[i]["codeDiff_len"] = len(item.get("diff", ""))

    transformed_data = [item for item in transformed_data if item["codeDiff"].strip()]
    examine_data = [item for item in examine_data if item["codeDiff"].strip()]

    for i, item in enumerate(transformed_data, 1):
        item["token_estimation"] = (len(item.get("comments", "")) + len(item.get("codeDiff", ""))) / 4
        processed_item = preprocess(item)
        # (len(item.get("codediff", 0)) > 5000 and len(item.get("codediff", 0) < 80000))
        if ((len(item.get("codeDiff", 0)) > 5000) and (len(item.get("codeDiff", 0)) < 80000)):
            index += 1
            processed_item["index"] = index
            final_data.append(processed_item)
        else:
            print(f"Removed codediff of length: {len(item.get("codeDiff", 0))}")

    index = 0

    for i, item in enumerate(examine_data, 1):
        
        if ((len(item.get("codeDiff", 0)) > 5000) and (len(item.get("codeDiff", 0)) < 80000)):
            index += 1
            item["index"] = index
            examine_final.append(item)
    
    output_file = f"../../data/iterations/examine/examine_data_iter{iteration}.json"

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(examine_final, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error: {str(e)}")
    
    print(f"Successfully transformed {len(final_data)} items")

    return final_data



def preprocess(data):
    return {
        "prompt" : [{"role": "user", "content": data["codeDiff"]}],
        "completion": [
            {"role": "assistant", "content": data["comments"]}
        ],
    }


# with open("../../data/pipeline/5_summarized_comments.json", "r", encoding='utf-8') as f:
#     summary_data = json.load(f)
# with open("../../data/pipeline/6_filtered_codediff.json", 'r', encoding='utf-8') as f:
#     codediff = json.load(f)

# data = get_model_data(summary_data, codediff)

# with open("../../data/model-training/critique_data2.json", "w", encoding='utf-8') as f:
#     json.dump(data, f, indent=2, ensure_ascii=False)
