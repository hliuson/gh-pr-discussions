# scripts/analyze_comments.py
import os
import sys
import json
import matplotlib.pyplot as plt

def analyze_comments(json_path: str):
    # 1) Load
    if not os.path.exists(json_path):
        print(f"❌ File not found at: {json_path}")
        return

    print(f"📄 Loading JSON from: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 2) Length distribution
    lengths = [item.get("comment_length", 0) for item in data if "comment_length" in item]
    if lengths:
        plt.hist(lengths, bins=30)
        plt.xlabel("Comment Length")
        plt.ylabel("Number of Comments")
        plt.title("Distribution of Comment Lengths")
        out_png = "comment_length_distribution.png"
        plt.savefig(out_png, bbox_inches="tight")
        plt.close()
        avg_len = sum(lengths) / len(lengths)
        print(f"✅ Plot saved as {out_png}")
        print(f"📊 Average length: {avg_len:.2f}")
        print(f"📉 Min length: {min(lengths)}, 📈 Max length: {max(lengths)}")
    else:
        print("⚠️ No comment_length field found in data.")

    # 3) Reason counts (why things get filtered)
    reason_counts = {}
    for item in data:
        reason = item.get("filter_reason")
        if reason:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

    print("\n=== FILTER REASONS (counts) ===")
    if reason_counts:
        # Sort by most frequent
        for r, c in sorted(reason_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"{r}: {c}")
    else:
        print("No filtering reasons found in data.")

    # 4) Classifier sanity check: show a few kept vs filtered
    kept = [c for c in data if not c.get("filter_reason")]
    filtered = [c for c in data if c.get("filter_reason")]

    def preview(items, label):
        print(f"\n=== {label} (first 3) ===")
        if not items:
            print("(none)")
            return
        for i, c in enumerate(items[:3], 1):
            body = (c.get("body") or "")[:200].replace("\n", " ")
            rid = c.get("comment_id") or c.get("pr_number") or "?"
            print(f"{i}. id={rid} | len={c.get('comment_length')} | {body}...")

    preview(kept, "KEPT")
    preview(filtered, "FILTERED")

if __name__ == "__main__":
    # If a path is provided, use it; otherwise default to project root JSON
    if len(sys.argv) >= 2:
        json_path = os.path.abspath(sys.argv[1])
    else:
        json_path = os.path.join(os.path.dirname(__file__), "..", "pr_discussions_cleaned.json")
        json_path = os.path.abspath(json_path)
    print(f"\n🔎 Looking for JSON file at: {json_path}\n")
    analyze_comments(json_path)

