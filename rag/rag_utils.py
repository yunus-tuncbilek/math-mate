# suppress warnings
import warnings
import os
from dotenv import load_dotenv

# Disable tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

warnings.filterwarnings("ignore")

# import libraries
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


def get_chunks(data_txt, chunk_size=512, overlap=128):
    """Split text into chunks (lecture-delimited if present, else fixed-size)."""
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

    return chunks


def get_embeddings(chunks, model_name="all-MiniLM-L6-v2"):
    """Generate embeddings for a list of text chunks."""
    if not chunks:
        print("No chunks provided for embedding generation")
        return None

    # Initialize sentence transformer model (cached across calls)
    model = _get_model(model_name)

    return model.encode(chunks)


def serialize_embedding(vec):
    """Pack a single embedding vector into raw float32 bytes for DB storage."""
    return np.asarray(vec, dtype=np.float32).tobytes()


def deserialize_embedding(blob):
    """Restore a 1-D float32 embedding from bytes written by serialize_embedding."""
    return np.frombuffer(blob, dtype=np.float32)


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
