import json

def transform_json_file(input_file, output_file):
    
    try:
        # Read the input JSON file
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Transform the data
        transformed_data = []
        index = 1
        for item in data[:34]:
            #print(f"Processing item with PR title: {item.get('pr_title', 'N/A')}")
            for comment in item.get("comments", []):
                transformed_item = {
                    "index": index,
                    "pr title": item.get("pr_title", ""),
                    "comment": comment,
                    "label": None
                }
                transformed_data.append(transformed_item)
                index += 1
        
        # Write the transformed data to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(transformed_data, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully transformed {len(transformed_data)} items")
        print(f"Output written to: {output_file}")
        
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file '{input_file}'")
    except Exception as e:
        print(f"Error: {str(e)}")

transform_json_file("../../data/pr_discussions_cleaned.json", "../../data/sentence-transformer/comments_for_labeling.json")