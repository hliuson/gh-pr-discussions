import json

def transform_json_file(input_file, output_file):
    
    try:
        # Read the input JSON file
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Transform the data
        transformed_data = []
        for item in data[:200]:
            transformed_item = {
                "pr body": item.get("pr_body", ""),
                "comment body": item.get("body", ""),
                "diff_length": item.get("diff_length", 0),
                "label": None
            }
            transformed_data.append(transformed_item)
        
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

transform_json_file("../../data/pr_discussions_cleaned.json", "../../data/filtered/comments_for_labeling.json")