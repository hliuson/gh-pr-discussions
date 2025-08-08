import json
import os

INPUT_FILE =  "../../data/sentence-transformer/comments_for_labeling.json"
OUTPUT_FILE = "../../data/sentence-transformer/labeled_comments1.json"

def load_comments():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ File {INPUT_FILE} not found.")
        return []
    with open(INPUT_FILE, "r") as f:
        return json.load(f)

def save_progress(data):
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"💾 Progress saved to {OUTPUT_FILE}")

def label_comment_interactive(comments):
    labeled = []
    print("  1 = Substantive")
    print("  0 = Low value (LGTM, nit, etc.)")
    print("  s = Skip")
    print("  q = Quit")
    for comment in comments:
        if comment.get("label") is not None:
            labeled.append(comment)
            continue

        print(f"\n\n\n📌 Comment {comment["index"]}:")
        print(comment["comment"])
        print("Label as:")
        

        while True:
            label = input("Your label: ").strip().lower()
            if label in ["1", "0"]:
                comment["label"] = int(label)
                labeled.append(comment)
                break
            elif label == "s":
                break
            elif label == "q":
                save_progress(labeled)
                return
            else:
                print("❗ Invalid input. Please enter 1, 0, s, or q.")

    save_progress(labeled)


comments = load_comments()
if comments:
    label_comment_interactive(comments)