from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import json
import numpy as np

# Load labeled data
with open("labeled_comments.json", "r") as f:
    data = json.load(f)

texts = [d["text"] for d in data if d["label"] is not None]
labels = [d["label"] for d in data if d["label"] is not None]

# Embed comments
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(texts)

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(embeddings, labels, test_size=0.2, random_state=42)

# Train classifier
clf = LogisticRegression()
clf.fit(X_train, y_train)

# Evaluate
y_pred = clf.predict(X_test)
print(classification_report(y_test, y_pred))
