import json

with open("pr_discussions_cleaned.json", "r") as f:
    comments = json.load(f)

# Extract just the comment text and metadata for labeling
labeling_data = [
    {"id": i, "text": item["body"], "label": None}
    for i, item in enumerate(comments)
]

with open("comments_for_labeling.json", "w") as f:
    json.dump(labeling_data, f, indent=2)

print("✅ comments_for_labeling.json created! Now open it and start labeling.")