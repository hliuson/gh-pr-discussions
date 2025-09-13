from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report, accuracy_score
import json
import numpy as np
import pandas as pd
import pickle
import joblib

# Load labeled data
with open("../../data/sentence-transformer/labeled_comments_formatted.json", "r", encoding="utf-8") as f:
    data = json.load(f)

texts = [d["text"] for d in data if d["label"] is not None]
labels = [d["label"] for d in data if d["label"] is not None]

# Embed comments
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(texts)

models = {
    'Logistic Regression': LogisticRegression(random_state=42),
    'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42),
    'XGBoost': XGBClassifier(random_state=42, eval_metric='logloss'),
    'SVM (RBF)': SVC(kernel='rbf', random_state=42, probability=True)
}

print("\n\n\nCross-validation comparison")
print("="*60)

cv_results = {}
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

for name, clf in models.items():
    scores = cross_val_score(clf, embeddings, labels, cv=cv, scoring = 'accuracy')
    cv_results[name] = {
        'mean': scores.mean(),
        'std': scores.std(),
        'scores': scores
    }
    print(f"{name:20}: {scores.mean():.3f} (+/- {scores.std() * 2:.3f})")

print("Detailed evaluation on test set")
print("="*60)

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(embeddings, labels, test_size=0.2, random_state=42)

test_results = {}

for name, clf in models.items():
    print(f"\n{name}")
    print("-" * 40)
    
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    test_results[name] = accuracy
    
    print(f"Test Accuracy: {accuracy:.3f}")
    print(classification_report(y_test, y_pred))

print("="*60)
print("FINAL COMPARISON")
print("="*60)

comparison_df = pd.DataFrame({
    'CV_Mean': [cv_results[name]['mean'] for name in models.keys()],
    'CV_Std': [cv_results[name]['std'] for name in models.keys()],
    'Test_Accuracy': [test_results[name] for name in models.keys()]
}, index=models.keys())

comparison_df = comparison_df.sort_values('CV_Mean', ascending=False)

print(comparison_df.round(3))

print(f"\nBest model (CV): {comparison_df.index[0]}")
print(f"Best model (Test): {max(test_results.items(), key=lambda x: x[1])[0]}")


# Find the best model
best_model_name = max(test_results.items(), key=lambda x: x[1])[0]
best_classifier = models[best_model_name]

# Train the best model on full dataset (optional - for better performance)
best_classifier.fit(embeddings, labels)  # Train on all data instead of just training split

# Save the sentence transformer model
model.save("../../models/sentence_transformer_model")

# Save the best classifier
with open("../../models/best_classifier.pkl", "wb") as f:
    pickle.dump(best_classifier, f)

# Save model metadata
model_info = {
    "best_model_name": best_model_name,
    "test_accuracy": test_results[best_model_name],
    "cv_mean": cv_results[best_model_name]['mean'],
    "cv_std": cv_results[best_model_name]['std']
}

with open("../../models/model_info.json", "w") as f:
    json.dump(model_info, f, indent=2)

print(f"\nModels saved:")
print(f"- Sentence Transformer: ../../models/sentence_transformer_model/")
print(f"- Best Classifier ({best_model_name}): ../../models/best_classifier.pkl")
print(f"- Model Info: ../../models/model_info.json")