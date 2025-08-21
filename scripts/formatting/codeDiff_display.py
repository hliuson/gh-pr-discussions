import json
import re

def getCodeDiff(input_file, output_file, index):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        codeDiff_list = []
        idx = 1
        for item in data:
            codeDiff = item.get("code_diff", "")
            filtered_codeDiff = filter_codediffs(codeDiff)

            transformed_codeDiff = {
                "index": idx,
                "codeDiff": filtered_codeDiff,
                "length": len(codeDiff),
                "filtered_codeDiff": filtered_codeDiff,
                "filtered_length": len(filtered_codeDiff)
            }

            codeDiff_list.append(transformed_codeDiff)
            idx += 1

        print(f"original length: {codeDiff_list[index].get("length", "")}")
        print(f"length after filtering: {codeDiff_list[index].get("filtered_length", "")}")

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(codeDiff_list, f, indent=2, ensure_ascii=False)
            #f.write(codeDiff_list)

    except FileNotFoundError:
        print(f"Error: Input file {input_file} not found.")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file '{input_file}'")
    except Exception as e:
        print(f"Error: {str(e)}")



def filter_codediffs(codeDiff):
    """Remove diffs that start with @@ -0,0"""
    pattern = r'diff --git.*?(?=diff --git|$)'
    
    def filter_diff(match):
        diff_block = match.group(0)
        # Check if block contains @@ with line numbers
        has_valid_hunk = re.search(r'@@\s*-\d+,\d+\s*\+\d+,\d+\s*@@', diff_block)
        if not has_valid_hunk:
            return ''
        
        def filter_small_diffs(match):
            full_hunk = match.group(0)
            header = match.group(1)
            
            # Extract the line counts from @@ -old_start,old_count +new_start,new_count @@
            numbers = re.findall(r'@@\s*-\d+,(\d+)\s*\+\d+,(\d+)\s*@@', header)
            if numbers:
                old_count = int(numbers[0][0])
                new_count = int(numbers[0][1]) 
                #print(f"{new_count} minus {old_count}")
                lines_changed = abs(new_count - old_count)
                
                # Keep only if 30+ lines changed
                return full_hunk if lines_changed >= 50 else ''
            
            return full_hunk

        # Apply small diff filter to this diff block
        hunk_pattern = r'(@@.*?@@)(.*?)(?=@@|$)'
        filtered_block = re.sub(hunk_pattern, filter_small_diffs, diff_block, flags=re.DOTALL)
        
        # Remove diff blocks that became empty after filtering small diffs
        if re.search(r'@@.*?@@', filtered_block):
            return filtered_block
        else:
            return ''

    
    return re.sub(pattern, filter_diff, codeDiff, flags=re.DOTALL)


getCodeDiff("../../data/filtered/filtered_critique_data.json", "../../data/model-training/codeDiff.json", 3)