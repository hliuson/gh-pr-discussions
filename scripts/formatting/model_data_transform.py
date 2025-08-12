import json

def get_model_data(input_file, output_file):
    
    try:
        with open(input_file, 'r', encoding="utf-8") as file:
            data = json.load(file)
        
        transformed_data = []
        for item in data:
            codeDiff = item.get("code_diff", "")
            comments = item.get("filtered_comments", "")
            combined_comments = ";\n".join(comments)
            token_estimation = (len(combined_comments) + len(codeDiff)) / 4

            transformed_item = {
                "comments": combined_comments,
                "codeDiff": codeDiff,
                "token_estimation": token_estimation
            }

            
            processed_item = preprocess(transformed_item)

            #print(processed_item)
            if(token_estimation < 32000):
                transformed_data.append(processed_item)

        with open(output_file, 'w', encoding="utf-8") as file:
            json.dump(transformed_data, file, indent=2, ensure_ascii=False)
        
        print(f"Successfully transformed {len(transformed_data)} items")
        print(f"Output written to: {output_file}")

    except FileNotFoundError:
        print(f"Error: Input file {input_file} not found.")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file '{input_file}'")
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

get_model_data("../../data/filtered/filtered_critique_data.json", "../../data/model-training/output.json")