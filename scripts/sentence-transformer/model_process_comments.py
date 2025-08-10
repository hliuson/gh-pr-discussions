from sentence_transformers import SentenceTransformer
import pickle
import json

def load_models():
    model = SentenceTransformer("../../models/sentence_transformer_model")
    with open("../../models/best_classifier.pkl", "rb") as f:
        classifier = pickle.load(f)

    with open("../../models/model_info.json", "r") as f:
        model_info = json.load(f)

    return model, classifier, model_info

    

def filter_comments(input_file, output_file, model, classifier):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        transformed_data = []
        index = 1
        for item in data:
            comments = item.get("comments", [])
            transformed_comments = []

            #print(comments)
            embeddings = model.encode(comments)
            predictions = classifier.predict(embeddings)
            probabilities = classifier.predict_proba(embeddings)

            comment_index = 0
            for comment, pred, prob in zip(comments, predictions, probabilities):
                if pred == 1:
                    transformed_comments.append(comment)
                    #print(f"\nComment index {comment_index} is substantial \n {comment[:100]} \n")
                else:
                    print(f"\nREMOVED comment {comment_index} ==== Score: {pred}(confidence: {prob}) ==== \nComment:{comment[:100]}\n")
                comment_index += 1

            transformed_item = {
                "index": index,
                "filtered_comments": transformed_comments,
                "code_diff": item.get("code_diff", "")
            }
            if item.get('code_diff') and len(transformed_comments) >= 4:
                transformed_data.append(transformed_item)
                index += 1
            elif not item.get('code_diff'):
                print("="*10)
                print(f"\n!!! REMOVED PR{item.get("pr_number")}, No code diff found\n")
                print("="*10)
            elif len(transformed_comments) < 4:
                print("="*10)
                print(f"\n!!! REMOVED PR{item.get("pr_number")}, comments left after filtering: {len(transformed_comments)}\n")
                print("="*10)
            
            
        
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

def test():
    model, classifier, model_info = load_models()

    print(f"Loaded {model_info['best_model_name']} with {model_info['test_accuracy']:.3f} accuracy")

    # Classify new data
    new_texts = ["This looks good to me", "This code is terrible", "Thank you for this thorough Ayrshare integration PR! The code looks well-structured with comprehensive implementation across both frontend and backend components.\n\nBefore this PR can be merged, there are a few items that need to be addressed:\n\n1. **Missing Checklist**: Please add the standard PR checklist from our template and check off the relevant items. Since this is a significant code change introducing new functionality, we need to ensure you've tested the implementation thoroughly.\n\n2. **Merge Conflicts**: The PR has the 'conflicts' label, indicating there are merge conflicts that need to be resolved before merging.\n\n3. **PR Title Scope**: Consider updating the PR title to use 'platform/blocks' as the scope instead of just 'block' to better align with our conventional commit format and labeled scopes.\n\n4. **Test Plan**: Please provide a test plan detailing how you've verified this integration works correctly. For example:\n   - Connecting to different social media platforms via Ayrshare\n   - Posting content to each supported platform\n   - Handling error cases (e.g., when profile key is missing)\n\nThe implementation itself looks solid, with proper security considerations and a clean architecture. Once the above items are addressed, this PR should be ready for final review."]
    embeddings = model.encode(new_texts)
    predictions = classifier.predict(embeddings)
    probabilities = classifier.predict_proba(embeddings)

    for text, pred, prob in zip(new_texts, predictions, probabilities):
        print(f"Comment: {text}")
        print(f"Prediction: {pred} (confidence: {max(prob):.3f})")

def run_classifier():
    model, classifier, model_info = load_models()
    filter_comments("../../data/filtered/unfiltered_critique_data.json", "../../data/filtered/filtered_critique_data.json", model, classifier)

run_classifier()