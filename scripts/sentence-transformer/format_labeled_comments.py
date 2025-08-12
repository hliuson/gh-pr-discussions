import json

def format_labeled_comments(input_file, output_file):

    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        formatted_data = []
        print(len(data))
        for item in data:
            transformed_data = {
                "text": item.get("comment", ""),
                "label": item.get("label", ""),
            }
            formatted_data.append(transformed_data)

        with open(output_file, 'w', encoding='utf-8') as file:
            file.write('[\n')
            for i, item in enumerate(formatted_data):
                json_str = json.dumps(item, separators=(',', ': '), ensure_ascii=False)
                if i < len(formatted_data) - 1:
                    file.write(json_str + ',\n')
                else:
                    file.write(json_str + '\n')
            file.write(']\n')

        print(f"Successfully transformed {len(formatted_data)} items")
        print(f"Output written to: {output_file}")
        
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file '{input_file}'")
    except Exception as e:
        print(f"Error: {str(e)}")

format_labeled_comments('../../data/sentence-transformer/labeled_comments.json', '../../data/sentence-transformer/labeled_comments_formatted.json')