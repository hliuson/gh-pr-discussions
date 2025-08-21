import json

def get_model_data(summary_file, codeDiff_file, output_file):

    transformed_data = []
    final_data = []

    try:
        with open(summary_file, 'r', encoding="utf-8") as file:
            summary = json.load(file)
        
        for item in summary:
            transformed_item = {
                "comments": item.get("summarized_comments", ""),
                "codeDiff": None,
                "token_estimation": None
            }

            transformed_data.append(transformed_item)

    except FileNotFoundError:
        print(f"Error: Input file {summary_file} not found.")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file '{summary_file}'")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    try:
        with open(codeDiff_file, 'r', encoding="utf-8") as file:
            cd = json.load(file)

        for i, item in enumerate(cd):
            transformed_data[i]["codeDiff"] = item.get("filtered_codeDiff", "")

        transformed_data = [item for item in transformed_data if item["codeDiff"].strip()]

        for i, item in enumerate(transformed_data):
            item["token_estimation"] = (len(item.get("comments", "")) + len(item.get("codeDiff", ""))) / 4

            processed_item = preprocess(item)

            #print(processed_item)
            if item.get("tokens", 0) < 32000:
                final_data.append(processed_item)
            else:
                print(f"Removed data with {item.get("tokens", 0)} tokens")

        with open(output_file, 'w', encoding="utf-8") as file:
            json.dump(final_data, file, indent=2, ensure_ascii=False)
        
        print(f"Successfully transformed {len(final_data)} items")
        print(f"Output written to: {output_file}")

    except FileNotFoundError:
        print(f"Error: Input file {codeDiff_file} not found.")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file '{codeDiff_file}'")
    except Exception as e:
        print(f"Error: {str(e)}")

def preprocess(data):
    return {
        "prompt" : [{"role": "user", "content": data["codeDiff"]}],
        "completion": [
            {"role": "assistant", "content": data["comments"]}
        ],
        "token_estimation": data["token_estimation"]
    }

get_model_data("../../data/model-training/summarized_comments.json", "../../data/model-training/codeDiff.json", "../../data/model-training/output1.json")