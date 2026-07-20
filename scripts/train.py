import argparse
import os
import sys
import joblib
import torch
import numpy as np
import pandas as pd
from pathlib import Path
from datasets import Dataset
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
    TrainingArguments,
    Trainer,
    set_seed
)

# Set seed for reproducibility
set_seed(42)

SUPPORTED_DOMAINS = ["AI", "ML", "DL", "NLP", "RL", "CV"]

# Premium mock dataset mapping query questions to domains
MOCK_DATA = [
    # AI - Artificial Intelligence
    {"query": "What is the history of Artificial Intelligence?", "Category": "AI"},
    {"query": "Explain weak AI vs strong AI systems.", "Category": "AI"},
    {"query": "What are the ethical implications of artificial general intelligence?", "Category": "AI"},
    {"query": "How is AI used in automated decision making systems?", "Category": "AI"},
    {"query": "What are the main components of an AI system?", "Category": "AI"},
    {"query": "Describe Turing test in artificial intelligence.", "Category": "AI"},
    {"query": "What are expert systems in artificial intelligence?", "Category": "AI"},
    {"query": "How does pathfinding algorithms like A* work in AI?", "Category": "AI"},
    {"query": "Explain symbolic AI vs connectionist AI.", "Category": "AI"},
    {"query": "How can AI solve complex planning tasks?", "Category": "AI"},
    
    # ML - Machine Learning
    {"query": "What is the difference between supervised and unsupervised learning?", "Category": "ML"},
    {"query": "How does a decision tree algorithm split data?", "Category": "ML"},
    {"query": "Explain bias-variance tradeoff in machine learning.", "Category": "ML"},
    {"query": "What is gradient descent and how is it used in regression?", "Category": "ML"},
    {"query": "How do support vector machines find the optimal hyperplane?", "Category": "ML"},
    {"query": "Describe k-means clustering algorithm steps.", "Category": "ML"},
    {"query": "What is cross validation in machine learning model evaluation?", "Category": "ML"},
    {"query": "Explain principal component analysis for dimensionality reduction.", "Category": "ML"},
    {"query": "What are ensemble methods like random forest and gradient boosting?", "Category": "ML"},
    {"query": "How does regularization (L1 and L2) prevent overfitting?", "Category": "ML"},

    # DL - Deep Learning
    {"query": "What is a neural network and how does backpropagation work?", "Category": "DL"},
    {"query": "Explain activation functions like ReLU, Sigmoid, and Tanh.", "Category": "DL"},
    {"query": "What are convolutional neural networks used for?", "Category": "DL"},
    {"query": "Explain vanishing and exploding gradient problems in deep networks.", "Category": "DL"},
    {"query": "What is dropout layer and how does it prevent overfitting in DL?", "Category": "DL"},
    {"query": "Describe the architecture of Recurrent Neural Networks.", "Category": "DL"},
    {"query": "What is generative adversarial network and how does it train?", "Category": "DL"},
    {"query": "Describe deep autoencoders and their reconstruction loss.", "Category": "DL"},
    {"query": "How does batch normalization speed up deep network training?", "Category": "DL"},
    {"query": "Explain self-attention mechanism in deep learning architectures.", "Category": "DL"},

    # NLP - Natural Language Processing
    {"query": "What is tokenization and lemmatization in text processing?", "Category": "NLP"},
    {"query": "Explain TF-IDF and bag of words models.", "Category": "NLP"},
    {"query": "How do word embeddings like Word2Vec and GloVe work?", "Category": "NLP"},
    {"query": "Explain the architecture of Transformer models in NLP.", "Category": "NLP"},
    {"query": "What is Named Entity Recognition and how is it built?", "Category": "NLP"},
    {"query": "How does BERT perform masked language modeling tasks?", "Category": "NLP"},
    {"query": "Explain sequence to sequence models for machine translation.", "Category": "NLP"},
    {"query": "How do we evaluate text generation models using BLEU and ROUGE?", "Category": "NLP"},
    {"query": "Explain sentiment analysis using recurrent network models.", "Category": "NLP"},
    {"query": "What is parser and dependency parsing in computational linguistics?", "Category": "NLP"},

    # RL - Reinforcement Learning
    {"query": "What is reinforcement learning and how is it different from ML?", "Category": "RL"},
    {"query": "Explain Markov Decision Processes framework in RL.", "Category": "RL"},
    {"query": "What is the exploration vs exploitation dilemma?", "Category": "RL"},
    {"query": "How does Q-learning update its Q-table values?", "Category": "RL"},
    {"query": "Explain policy gradient methods and Actor-Critic architectures.", "Category": "RL"},
    {"query": "What is deep Q-network and how does it use experience replay?", "Category": "RL"},
    {"query": "Describe reward shaping and policy optimization in RL.", "Category": "RL"},
    {"query": "What is temporal difference learning in reinforcement learning?", "Category": "RL"},
    {"query": "Explain Monte Carlo tree search and its integration with RL.", "Category": "RL"},
    {"query": "What are model-based vs model-free reinforcement learning algorithms?", "Category": "RL"},

    # CV - Computer Vision
    {"query": "What is image segmentation and how does U-Net architecture work?", "Category": "CV"},
    {"query": "Explain object detection models like YOLO and Faster R-CNN.", "Category": "CV"},
    {"query": "How does edge detection like Canny edge detector function?", "Category": "CV"},
    {"query": "What are image kernels and convolution operations in CV?", "Category": "CV"},
    {"query": "Explain optical flow and motion tracking in video analysis.", "Category": "CV"},
    {"query": "Describe feature matching algorithms like SIFT and ORB.", "Category": "CV"},
    {"query": "How does image classification using ResNet skip connections work?", "Category": "CV"},
    {"query": "Explain transfer learning for custom computer vision models.", "Category": "CV"},
    {"query": "What is data augmentation and how does it help vision models?", "Category": "CV"},
    {"query": "Explain 3D computer vision and stereo depth estimation.", "Category": "CV"}
]

def generate_mock_dataset(path: str) -> pd.DataFrame:
    """Generate a clean mock dataset of 60 rows matching 6 domains for bootstrapping"""
    print(f"Creating a bootstrap mock dataset at {path}...")
    df = pd.DataFrame(MOCK_DATA)
    # Replicate data to make a decent training size
    replicated = []
    for _ in range(5):
        for item in MOCK_DATA:
            # Add small noise/variation to avoid perfect duplicates
            replicated.append({
                "query": item["query"] + " " + np.random.choice(["Explain.", "Describe details.", "Provide details.", ""]),
                "Category": item["Category"]
            })
    full_df = pd.DataFrame(replicated)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    full_df.to_csv(path, index=False)
    print(f"Mock dataset generated successfully with {len(full_df)} rows.")
    return full_df

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, average="weighted"
    )
    accuracy = accuracy_score(labels, preds)
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }

def main():
    parser = argparse.ArgumentParser(description="Fine-tune DistilBERT Sequence Classifier for Domain Routing")
    parser.add_argument("--data_path", type=str, default="workspace/data/domain_dataset.csv", help="Path to classification CSV dataset")
    parser.add_argument("--output_dir", type=str, default="workspace/models/distilbert_model", help="Directory to save the trained model")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=8, help="Batch size for training and evaluation")
    parser.add_argument("--learning_rate", type=float, default=2e-5, help="Learning rate for optimization")
    args = parser.parse_args()

    # Load or generate dataset
    if not os.path.exists(args.data_path):
        df = generate_mock_dataset(args.data_path)
    else:
        print(f"Loading dataset from: {args.data_path}")
        df = pd.read_csv(args.data_path)

    # Preprocess dataset
    df = df.dropna(subset=["query", "Category"])
    df = df.drop_duplicates(subset=["query"])
    # Standardize Category name
    df["Category"] = df["Category"].str.strip().str.upper()
    df = df[df["Category"].isin(SUPPORTED_DOMAINS)]
    df.reset_index(drop=True, inplace=True)

    print(f"Dataset shape after cleaning: {df.shape}")
    print("Class distribution:\n", df["Category"].value_counts())

    if len(df) < 10:
        print("Error: Dataset is too small to train safely. Must have at least 10 entries.")
        sys.exit(1)

    # Fit and save LabelEncoder
    label_encoder = LabelEncoder()
    df["label"] = label_encoder.fit_transform(df["Category"])
    
    os.makedirs(args.output_dir, exist_ok=True)
    encoder_path = os.path.join(args.output_dir, "label_encoder.pkl")
    joblib.dump(label_encoder, encoder_path)
    print(f"LabelEncoder saved to {encoder_path}. Classes: {label_encoder.classes_}")

    # Split dataset (stratified split)
    train_df, val_df = train_test_split(
        df, test_size=0.2, stratify=df["label"], random_state=42
    )
    print(f"Training samples: {len(train_df)} | Validation samples: {len(val_df)}")

    # Convert pandas dataframes to HuggingFace datasets
    train_dataset = Dataset.from_pandas(train_df)
    val_dataset = Dataset.from_pandas(val_df)

    # Initialize Tokenizer
    print("Loading distilbert-base-uncased tokenizer...")
    tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")

    def tokenize(batch):
        return tokenizer(
            batch["query"], padding="max_length", truncation=True, max_length=128
        )

    print("Tokenizing datasets...")
    train_dataset = train_dataset.map(tokenize, batched=True)
    val_dataset = val_dataset.map(tokenize, batched=True)

    # Rename label column to match trainer standards
    train_dataset = train_dataset.rename_column("label", "labels")
    val_dataset = val_dataset.rename_column("label", "labels")

    # Keep only columns used by PyTorch model
    cols = ["query", "Category", "Topic", "__index_level_0__"]
    for col in cols:
        if col in train_dataset.column_names:
            train_dataset = train_dataset.remove_columns(col)
        if col in val_dataset.column_names:
            val_dataset = val_dataset.remove_columns(col)

    # Load Model
    print(f"Loading DistilBERT for classification with {len(label_encoder.classes_)} labels...")
    model = DistilBertForSequenceClassification.from_pretrained(
        "distilbert-base-uncased", num_labels=len(label_encoder.classes_)
    )

    # Define training arguments
    results_dir = "./results"
    training_args = TrainingArguments(
        output_dir=results_dir,
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_strategy="epoch",
        learning_rate=args.learning_rate,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        num_train_epochs=args.epochs,
        weight_decay=0.01,
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
        report_to="none",
        fp16=torch.cuda.is_available()
    )

    # Initialize Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics
    )

    # Run Training
    print("Starting DistilBERT fine-tuning...")
    trainer.train()

    # Save fine-tuned model and tokenizer
    print(f"Saving fine-tuned model and tokenizer to {args.output_dir}...")
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    
    # Save a configuration copy of classes inside the model config
    model.config.id2label = {int(i): label for i, label in enumerate(label_encoder.classes_)}
    model.config.label2id = {label: int(i) for i, label in enumerate(label_encoder.classes_)}
    model.config.save_pretrained(args.output_dir)

    print("Evaluating model performance on validation set...")
    val_results = trainer.evaluate(val_dataset)
    print(f"Validation Results: {val_results}")
    print("Fine-tuning completed successfully!")

if __name__ == "__main__":
    main()
