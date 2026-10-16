"""
Problem 3.1: Supervised Classifier Comparison on the Iris dataset.

Trains five classic classifiers and prints a benchmark table of
Accuracy, Precision, Recall, and F1-Score (macro-averaged) on a held-out test set.
"""
import numpy as np
import pandas as pd
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.metrics import (classification_report, f1_score, accuracy_score,
                             precision_score, recall_score)
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB

# Load data and split (70% train / 30% test)
data = load_iris()
X_train, X_test, y_train, y_test = train_test_split(
    data.data, data.target, test_size=0.3, random_state=42
)

models = {
    "Logistic Regression": LogisticRegression(max_iter=200),
    "KNN (K=5)": KNeighborsClassifier(n_neighbors=5),
    "SVM (RBF)": SVC(kernel='rbf'),
    "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
    "Gaussian Naive Bayes": GaussianNB()
}

# Fit each model on X_train, evaluate metrics on X_test
results = []
for name, model in models.items():
    model.fit(X_train, y_train)          # learn from training data
    y_pred = model.predict(X_test)       # predict unseen test data

    results.append({
        "Model": name,
        "Accuracy": accuracy_score(y_test, y_pred),
        "Precision": precision_score(y_test, y_pred, average="macro"),
        "Recall": recall_score(y_test, y_pred, average="macro"),
        "F1-Score": f1_score(y_test, y_pred, average="macro"),
    })

    # Optional per-class detail for each model
    print(f"\n=== {name} ===")
    print(classification_report(y_test, y_pred,
                                target_names=data.target_names, digits=4))

# Build and print the summary benchmark table
df = pd.DataFrame(results).set_index("Model")
df = df.sort_values("F1-Score", ascending=False)

print("\n" + "=" * 70)
print("Classifier Benchmark on Iris (test set, n = {}, macro-averaged)".format(len(y_test)))
print("=" * 70)
print(df.to_string(float_format=lambda v: f"{v:.4f}"))
print("=" * 70)
