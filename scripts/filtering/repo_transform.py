
import json

def transform_repo_format(input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data=json.load(f)
        
        transformed_data = []
        for item in data:
            transformed_item = {
                "full_name": item.get("full_name", ""),
                "description": item.get("description", ""),
            }
            transformed_data.append(transformed_item)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(transformed_data, f, indent=2, ensure_ascii=False)

        print(f"Successfully transformed {len(data)} items")
        print(f"Transformed data saved to {output_file}")

    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file '{input_file}'")
    except Exception as e:
        print(f"Error: {str(e)}")

transform_repo_format('../../data/high_quality_repos.json', '../../data/transformed_repos.json')
