# EduQuery AI – Landing Page README

## Project Overview

This landing page showcases **EduQuery AI**, an intelligent educational assistant that leverages **Fine-Tuned DistilBERT** and **Retrieval-Augmented Generation (RAG)** to provide accurate, domain-specific answers for Artificial Intelligence-related educational queries.

Unlike conventional question-answering systems that search every available resource, EduQuery AI first predicts the subject of the user's query and then retrieves information only from the most relevant knowledge source. This targeted retrieval approach improves response speed, enhances answer accuracy, and reduces unnecessary document searching.

The landing page is designed as a modern, professional portfolio website that clearly explains the project's purpose, workflow, architecture, technologies, and performance.

---

# Website Structure

The website consists of **5 main sections**.

---

# Page 1 – Hero Section

## Purpose

Introduce the project and provide users with a clear understanding of what the application does.

### Content

### Hero Title

**EduQuery AI**

### Hero Subtitle

*Domain-Specific Educational Assistant using Fine-Tuned DistilBERT & Retrieval-Augmented Generation (RAG).*

### Introduction

Provide a brief overview explaining that the system classifies educational queries into AI domains before retrieving information, resulting in faster and more relevant responses.

### About the Project

Explain that the platform combines:

* Fine-Tuned DistilBERT
* Intelligent Routing
* Retrieval-Augmented Generation (RAG)
* PDF Processing
* CSV Analysis
* Knowledge Base Search

### Supported Domains

Display six cards:

* Machine Learning
* Deep Learning
* Natural Language Processing
* Computer Vision
* Reinforcement Learning
* Artificial Intelligence

### Feature Cards

Include attractive feature cards such as:

* Domain Classification
* PDF Question Answering
* CSV Data Analysis
* Intelligent Routing
* RAG-based Responses
* Semantic Search
* Fast Retrieval
* Subject-specific Knowledge Base

### Suggested CTA Buttons

* Explore Workflow
* View Architecture
* View Results

---

# Page 2 – Technology Stack & Workflow

## Purpose

Explain the technologies used and how the system works internally.

---

## Technology Stack

Divide the technologies into categories.

### Artificial Intelligence

* DistilBERT
* Hugging Face Transformers
* Sentence Transformers
* Retrieval-Augmented Generation (RAG)

### Backend

* Python
* FastAPI

### Vector Search

* FAISS

### Data Processing

* Pandas
* NumPy
* Scikit-learn

### Deployment

* Docker

---

## Workflow Diagram

Create a professional flowchart similar to:

```
User Query
      │
      ▼
Fine-Tuned DistilBERT
(Domain Classification)
      │
      ▼
Routing Agent
      │
 ┌───────────────┬───────────────┬──────────────┐
 │               │               │
 ▼               ▼               ▼
PDF Tool     CSV Analyzer   Knowledge Base
 │               │               │
 └───────────────┴───────────────┘
                 │
                 ▼
Sentence Transformers
                 │
                 ▼
FAISS Vector Search
                 │
                 ▼
Relevant Context
                 │
                 ▼
Large Language Model (RAG)
                 │
                 ▼
Final Response
```

---

# Page 3 – System Architecture

## Purpose

Display the complete architecture of the system.

Create a modern architecture diagram with different layers.

```
                    USER

                      │

                 User Query

                      │

           Fine-Tuned DistilBERT

           Domain Classification

                      │

              Intelligent Agent

       ┌────────┬──────────┬─────────┐
       │        │          │
       ▼        ▼          ▼

 PDF Retrieval  CSV Tool  Knowledge Base

       │        │          │

       └────────┴──────────┘

      Sentence Transformers

              │

         FAISS Database

              │

      Relevant Chunks

              │

        Large Language Model

              │

       Generated Response
```

---

## Architecture Description

Below the architecture diagram, include a short explanation describing how the classifier predicts the query domain before retrieval, enabling faster searches and more relevant responses.

---

# Page 4 – Model Performance

## Purpose

Present the performance of the trained DistilBERT model using attractive visualizations.

---

## Performance Metrics

Display four metric cards.

| Metric    | Value  |
| --------- | ------ |
| Accuracy  | 70.86% |
| Precision | 64.19% |
| Recall    | 70.86% |
| F1 Score  | 66.97% |

---

## Confusion Matrix

Display the confusion matrix image from the project.

Include a short explanation highlighting that most classes are predicted correctly, while Deep Learning and Machine Learning exhibit some overlap due to similar semantic contexts.

---

## Graphical Representation

Include the following charts.

### Accuracy Bar Chart

Display bars for:

* Accuracy
* Precision
* Recall
* F1 Score

---

### Circular Progress Indicators

Represent:

* Accuracy
* Precision
* Recall
* F1 Score

using animated circular progress components.

---

### Radar Chart

Visualize all four evaluation metrics in a radar chart for an intuitive comparison.

---

## Performance Highlights

Display quick statistics such as:

* Faster Retrieval
* Reduced Search Space
* Context-aware Responses
* Domain-specific Classification
* Improved Educational Assistance

---

# Page 5 – Project Highlights & Future Scope

## Purpose

Summarize the project and present its advantages and future enhancements.

---

## Why EduQuery AI?

Explain that the system performs domain prediction before retrieval, making the assistant significantly more efficient than conventional educational chatbots.

---

## Advantages

Display feature cards including:

* Fine-Tuned DistilBERT
* Intelligent Query Routing
* Retrieval-Augmented Generation
* Semantic Search
* PDF Support
* CSV Analysis
* FastAPI Backend
* Docker Deployment
* Scalable Architecture

---

## Future Scope

Display the future improvements as cards.

Suggested cards:

* Multilingual Support
* Voice Assistant
* OCR Support
* Cloud Deployment
* Additional Technical Domains
* Personalized Learning
* Educational Analytics Dashboard
* Live Knowledge Integration

---

# UI Design Guidelines

## Theme

* Clean Minimal Design
* Use same colour coding as used rn 

---

## Animations

Use smooth animations throughout the landing page.

Examples:

* Fade In
* Slide Up
* Zoom In
* Scroll Reveal
* Hover Scaling
* Floating Icons
* Animated Cards

---

## Icons

Recommended icon libraries:

* Lucide React
* Heroicons
* React Icons

---





# Recommended Tech Stack for Landing Page

* React.js / Next.js
* Tailwind CSS
* Framer Motion
* TypeScript
* Lucide React Icons
* Chart.js or Recharts (for graphs)
* React Flow (optional for workflow diagrams)

---

# Deliverables

The final landing page should include:

* Responsive Design
* Hero Section
* About Section
* Feature Cards
* Technology Stack
* Workflow Diagram
* System Architecture
* Performance Dashboard
* Confusion Matrix
* Charts (Bar, Circular Progress, Radar)
* Project Advantages
* Future Scope
* Professional Footer with project details

---

# Goal

The objective of this landing page is to professionally present **EduQuery AI** as an intelligent, domain-aware educational assistant. It should clearly demonstrate the project's methodology, technical implementation, system architecture, and evaluation results while providing visitors with an engaging and visually appealing experience.
