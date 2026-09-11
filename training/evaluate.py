import os
import csv
from pathlib import Path
import joblib
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
# Import transformer class so unpickler finds it
from train import PairFeatureExtractor, load_data

def evaluate_model():
    base_dir = Path(__file__).resolve().parent
    dataset_file = base_dir / "dataset.csv"
    model_path = base_dir / "model" / "classifier.joblib"

    if not model_path.exists():
        print(f"Trained model not found at {model_path}. Please run train.py first.")
        return

    print(f"Loading model from {model_path}...")
    model = joblib.load(model_path)

    print(f"Loading evaluation dataset from {dataset_file}...")
    X, y = load_data(str(dataset_file))

    y_pred = model.predict(X)
    acc = accuracy_score(y, y_pred)
    cm = confusion_matrix(y, y_pred)

    print("\n==========================================")
    print("EVALUATION RESULTS")
    print("==========================================")
    print(f"Total evaluated samples: {len(y)}")
    print(f"Overall Accuracy: {acc * 100:.2f}%\n")
    print("Confusion Matrix:")
    print("                Pred Grounded   Pred Hallucinated")
    print(f"True Grounded         {cm[0][0]:<15} {cm[0][1]}")
    print(f"True Hallucinated     {cm[1][0]:<15} {cm[1][1]}\n")
    print("Detailed Classification Report:")
    print(classification_report(y, y_pred, target_names=["GROUNDED (0)", "HALLUCINATED (1)"]))

if __name__ == "__main__":
    evaluate_model()
