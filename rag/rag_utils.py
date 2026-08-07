# suppress warnings
import warnings
import os
from dotenv import load_dotenv

# Disable tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

warnings.filterwarnings("ignore")

# import libraries
import json
import pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()


# The SentenceTransformer model is loaded lazily and cached, so that (a) merely
# importing this module doesn't drag in torch (keeping `flask run` fast) and
# (b) the model weights are loaded only once instead of on every RAG call.
_model_cache = {}


def _get_model(model_name="all-MiniLM-L6-v2"):
    """Return a cached SentenceTransformer, loading it on first use."""
    if model_name not in _model_cache:
        from sentence_transformers import SentenceTransformer

        _model_cache[model_name] = SentenceTransformer(model_name)
    return _model_cache[model_name]


def load_data(file_path):
    """Load lecture data from text file."""
    assert os.path.exists(file_path), f"File not found: {file_path}"

    with open(file_path, "r", encoding="utf-8") as f:
        data_txt = f.read()

    print(f"Loaded data from {file_path}")
    return data_txt


def get_chunks(data_txt, save_to=None, chunk_size=512, overlap=128):
    """Split data into chunks and optionally save to file."""
    # Check if data contains lectures, which must start with "Lecture"
    if "Lecture" in data_txt:
        lectures = data_txt.split("Lecture")

        chunks = []
        for record in lectures:
            if record.strip():  # Skip empty records
                # Add back the "Lecture:" prefix and clean up
                full_record = "Lecture" + record.strip()
                chunks.append(full_record)

        print(f"Created {len(chunks)} chunks from lecture data")
    else:
        # No structured lecture IDs found, 
        # create fixed-size chunks with overlap
        chunks = []
        start = 0

        while start < len(data_txt):
            # Get chunk from start to start + chunk_size
            end = min(start + chunk_size, len(data_txt))
            chunk = data_txt[start:end]

            # Only add non-empty chunks
            if chunk.strip():
                chunks.append(chunk.strip())

            # Move start position by (chunk_size - overlap) for next chunk
            # This creates overlap between consecutive chunks
            start += chunk_size - overlap

            # Break if we've reached the end
            if end >= len(data_txt):
                break

        print(
            f"Created {len(chunks)} chunks of {chunk_size} characters with {overlap} character overlap"
        )

    # Save chunks if requested
    if save_to:
        with open(save_to, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=2)
        # print(f"Chunks saved to {save_to}")

    return chunks


def get_embeddings(chunks, save_to=None, model_name="all-MiniLM-L6-v2"):
    """Generate embeddings for chunks and optionally save to file."""
    if not chunks:
        print("No chunks provided for embedding generation")
        return None

    # Initialize sentence transformer model (cached across calls)
    model = _get_model(model_name)

    # Generate embeddings
    embeddings = model.encode(chunks)

    # print(f"Generated embeddings for {len(chunks)} chunks using {model_name}")

    # Save embeddings if requested
    if save_to:
        with open(save_to, "wb") as f:
            pickle.dump(embeddings, f)
        # print(f"Embeddings saved to {save_to}")

    return embeddings


def retrieve_closest_chunk(
    query, chunks, embeddings, top_k=1, model_name="all-MiniLM-L6-v2"
):
    """Retrieve the closest chunk(s) to the query."""
    if not chunks or embeddings is None:
        return None, None, None, None, None

    # Initialize model for query encoding (cached across calls)
    model = _get_model(model_name)

    # Generate embedding for the query
    query_embedding = model.encode([query])

    # Calculate cosine similarity
    similarities = cosine_similarity(query_embedding, embeddings)[0]

    # Get top-k most similar chunks
    top_indices = np.argsort(similarities)[::-1][:top_k]

    if top_k == 1:
        # Return single closest chunk
        best_idx = top_indices[0]
        return (
            chunks[best_idx],
            similarities[best_idx],
            best_idx,
            query_embedding,
            similarities,
        )
    else:
        # Return multiple chunks
        closest_chunks = []
        closest_similarities = []
        closest_indices = []

        for idx in top_indices:
            closest_chunks.append(chunks[idx])
            closest_similarities.append(similarities[idx])
            closest_indices.append(idx)

        return (
            closest_chunks,
            closest_similarities,
            closest_indices,
            query_embedding,
            similarities,
        )

def load_chunks(file_path):
    """Load chunks from a JSON file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Chunks file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_embeddings(file_path):
    """Load embeddings from a pickle file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Embeddings file not found: {file_path}")
    with open(file_path, "rb") as f:
        return pickle.load(f)
