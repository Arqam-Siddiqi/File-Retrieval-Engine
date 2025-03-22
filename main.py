from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Load SBERT model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Example documents
documents = [
    "Deep learning has revolutionized computer vision, enabling machines to perform tasks like image recognition, object detection, and segmentation with high accuracy.",
    "Neural networks are a type of machine learning model inspired by the structure of the brain. They are commonly used for classification tasks, such as identifying objects in images.",
    "Natural language processing (NLP) is a subfield of artificial intelligence that focuses on the interaction between computers and human language, including tasks like translation and sentiment analysis.",
    "Convolutional neural networks (CNNs) are a class of deep neural networks specifically designed for image processing tasks. They use convolutional layers to detect patterns in images."
]

# Generate embeddings for each document
document_embeddings = model.encode(documents, convert_to_tensor=True)

# Convert to numpy arrays for cosine similarity
document_embeddings_np = document_embeddings.cpu().numpy()

# Example query
query = "Explain how computers can convert information into human-readable format"

# Generate embedding for the query
query_embedding = model.encode(query, convert_to_tensor=True)

# Reshape the query embedding to 2D (1, N)
query_embedding = query_embedding.cpu().numpy().reshape(1, -1)  # Ensuring it's 2D

# Calculate cosine similarity
cosine_similarities = cosine_similarity(query_embedding, document_embeddings_np)

# Get the indices of the top 3 most similar documents
top_k_indices = cosine_similarities[0].argsort()[-3:][::-1]  # Top 3

# Print the results
print("Top 3 Relevant Documents:")
for idx in top_k_indices:
    print(f"Document {idx+1}: {documents[idx]}")
