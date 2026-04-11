import numpy as np
import pandas as pd
from utils.embedding import get_embedding

try:
    import faiss  # type: ignore
except ModuleNotFoundError:
    faiss = None

# Load your dataset
data = pd.read_csv("data/complaints.csv")

# Convert complaints to embeddings
embeddings = np.asarray(
    [get_embedding(text) for text in data["Complaint"]],
    dtype="float32",
)

dimension = embeddings.shape[1]

index = None
if faiss is not None:
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

def search_similar(query, k=2):
    query_vector = np.asarray([get_embedding(query)], dtype="float32")

    if index is not None:
        _, indices = index.search(query_vector, k)
    else:
        # Fall back to a NumPy distance search when FAISS is unavailable.
        distances = np.linalg.norm(embeddings - query_vector, axis=1)
        indices = np.argsort(distances)[:k].reshape(1, -1)

    results = data.iloc[indices[0]]
    return results
