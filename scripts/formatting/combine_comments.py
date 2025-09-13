
import json

def combine(input1, input2, output):

    item_list = []
    comment_list = []

    try:
        with open(input1, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for i, item in enumerate(data, 1):
            transformed_item = {
                "index": i,
                "unsummarized": item.get("unsumarized_comments", ""),
                "summarized_old": item.get("summarized_comments", ""),
                "old_length": len(item.get("summarized_comments", "")),
                "summarized_new": None,
                "new_length": None
            }
            item_list.append(transformed_item)
        
    except FileNotFoundError:
        print(f"Error: Input file {input1} not found.")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file '{input1}'")
    except Exception as e:
        print(f"Error: {str(e)}")

    try:
        with open(input2, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for i, item in enumerate(data):
            item_list[i]["summarized_new"] = item.get("summarized_comments", "")
            item_list[i]["new_length"] = len(item.get("summarized_comments", ""))
            comment_list.append(item_list[i])

        with open(output, 'w', encoding='utf-8') as f:
            json.dump(comment_list, f, indent=2, ensure_ascii=False)
        
    except FileNotFoundError:
        print(f"Error: Input file {input2} not found.")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file '{input2}'")
    except Exception as e:
        print(f"Error: {str(e)}")
        
if __name__ == "__main__":
    combine("../../data/pipeline/5_summarized_comments.json", "../../data/pipeline/5_summarized_comments1.json", "../../data/filtered/combined_comments.json")