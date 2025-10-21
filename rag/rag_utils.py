# suppress warnings
import warnings
import os
from dotenv import load_dotenv

# Disable tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

warnings.filterwarnings("ignore")

# import libraries
import requests, os
import json
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from together import Together
import textwrap
# from sklearn.manifold import TSNE
import plotly.express as px
import plotly.graph_objects as go
from bs4 import BeautifulSoup
import time

load_dotenv()

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
client = Together(api_key=TOGETHER_API_KEY)


## FUNCTION 1: This Allows Us to Prompt the AI MODEL
# -------------------------------------------------
def prompt_llm(prompt, with_linebreak=False):
    # This function allows us to prompt an LLM via the Together API

    # model
    model = "meta-llama/Meta-Llama-3-8B-Instruct-Lite"

    # Make the API call
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    output = response.choices[0].message.content

    if with_linebreak:
        # Wrap the output
        wrapped_output = textwrap.fill(output, width=50)

        return wrapped_output
    else:
        return output


def load_data(file_path):
    """Load patient data from text file."""
    assert os.path.exists(file_path), f"File not found: {file_path}"

    with open(file_path, "r", encoding="utf-8") as f:
        data_txt = f.read()

    print(f"Loaded data from {file_path}")
    return data_txt


def get_chunks(data_txt, save_to=None, chunk_size=512, overlap=128):
    """Split data into chunks and optionally save to file."""
    # Check if data contains patient records (with "PATIENT ID:")
    if "Lecture" in data_txt:
        # Split by patient records (each patient starts with "Lecture:")
        patient_records = data_txt.split("Lecture")

        chunks = []
        for record in patient_records:
            if record.strip():  # Skip empty records
                # Add back the "Lecture:" prefix and clean up
                full_record = "Lecture" + record.strip()
                chunks.append(full_record)

        print(f"Created {len(chunks)} chunks from patient data")
    else:
        # No patient IDs found, create fixed-size chunks with overlap
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

    # Initialize sentence transformer model
    model = SentenceTransformer(model_name)

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

    # Initialize model for query encoding
    model = SentenceTransformer(model_name)

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


def get_rag_with_chunk(query, closest_chunk, chunk_index=None, save_to=None):
    """Generate RAG response using the closest chunk and prompt_llm."""
    if not closest_chunk:
        return "No relevant information found.", None, None

    # Create prompt for the LLM
    prompt = f"""Please answer the user's question based on the following information.

<INFOMATION>
{closest_chunk}
</INFOMATION>

<USER QUESTION>
{query}
</USER QUESTION>

Please provide a helpful and accurate response based on the information provided.

* instructions:
- limit your response to be 2 lines max (10 words each)
"""

    # Get response from LLM
    rag_output = "\nAI: " + prompt_llm(prompt) + "\n\n"

    if save_to:
        with open(save_to + "/rag_response.txt", "w") as f:
            f.write(rag_output)
        # print(f"RAG response saved to {save_to}")

        with open(save_to + "/rag_prompt.txt", "w") as f:
            f.write(prompt)
        # print(f"RAG prompt saved to {save_to}")

    return rag_output, closest_chunk, chunk_index


def load_html_page(
    url="https://en.wikipedia.org/wiki/HealthLinkBC", output_file="data/healthbc.txt"
):
    """
    Load content from HealthLinkBC Wikipedia page and save it to a text file.

    Args:
        url (str): The URL to scrape content from (default: HealthLinkBC Wikipedia)
        output_file (str): Path to save the scraped content (default: data/healthbc.txt)

    Returns:
        str: The scraped content text
    """

    print(f"Loading content from {url}...")

    # Set up headers to mimic a real browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    # Make the request
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()  # Raise an exception for bad status codes

    # Parse the HTML content
    soup = BeautifulSoup(response.content, "html.parser")

    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()

    # Extract paragraphs and filter by length
    paragraphs = soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6"])
    filtered_paragraphs = []

    for para in paragraphs:
        text_content = para.get_text().strip()
        # Only keep paragraphs with at least 30 characters
        if len(text_content) >= 30:
            filtered_paragraphs.append(text_content)

    # Join paragraphs with double newlines
    text = "\n\n".join(filtered_paragraphs)

    # Format text with line breaks every 80 characters
    formatted_lines = []
    for paragraph in filtered_paragraphs:
        # Split paragraph into lines of 80 characters max
        words = paragraph.split()
        current_line = ""

        for word in words:
            # Check if adding this word would exceed 80 characters
            if len(current_line + " " + word) <= 80:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
            else:
                # Add current line and start new line with current word
                if current_line:
                    formatted_lines.append(current_line)
                current_line = word

        # Add the last line if it exists
        if current_line:
            formatted_lines.append(current_line)

        # Add empty line between paragraphs
        formatted_lines.append("")

    # Join all lines with newlines
    text = "\n".join(formatted_lines)

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Save to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(text)

    # print(f"Content successfully saved to {output_file}")
    # print(f"Content length: {len(text)} characters")

    return text


def load_html_page_with_delay(
    url="https://en.wikipedia.org/wiki/HealthLinkBC",
    output_file="data/healthbc.txt",
    delay=2,
):
    """
    Load content from HealthLinkBC Wikipedia page with delay and save it to a text file.
    This version includes a delay to be respectful to the server.

    Args:
        url (str): The URL to scrape content from (default: HealthLinkBC Wikipedia)
        output_file (str): Path to save the scraped content (default: data/healthbc.txt)
        delay (int): Delay in seconds before making the request (default: 2)

    Returns:
        str: The scraped content text
    """
    print(f"Waiting {delay} seconds before making request...")
    time.sleep(delay)

    return load_html_page(url, output_file)


def visualize_embeddings_1d(
    chunks,
    chunk_embeddings,
    query,
    query_embedding,
    title="1D Similarity Visualization",
):
    """
    Create a 1D bar chart visualization of similarity scores between query and chunks.

    Args:
        chunks: List of text chunks
        chunk_embeddings: Numpy array of chunk embeddings
        query: Query text string
        query_embedding: Numpy array of query embedding
        title: Title for the plot (default: "1D Similarity Visualization")

    Returns:
        plotly.graph_objects.Figure: Interactive bar chart figure
    """
    from sklearn.metrics.pairwise import cosine_similarity

    # Ensure query_embedding is 2D
    if query_embedding.ndim == 1:
        query_embedding = query_embedding.reshape(1, -1)

    # Calculate cosine similarity between query and all chunks
    similarities = cosine_similarity(query_embedding, chunk_embeddings)[0]

    # Create chunk labels and hover text
    chunk_labels = [f"Chunk {i+1}" for i in range(len(chunks))]
    chunk_hover_texts = [
        chunk[:100] + "..." if len(chunk) > 100 else chunk for chunk in chunks
    ]

    # Create color mapping based on similarity scores
    # Higher similarity = more red, lower similarity = more blue
    colors = []
    for sim in similarities:
        if sim > 0.7:
            colors.append("red")
        elif sim > 0.5:
            colors.append("orange")
        elif sim > 0.3:
            colors.append("yellow")
        else:
            colors.append("lightblue")

    # Create the bar chart
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=chunk_labels,
            y=similarities,
            marker=dict(color=colors, line=dict(width=1, color="black")),
            text=[f"{sim:.3f}" for sim in similarities],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>"
            + "Similarity: %{y:.3f}<br>"
            + "Content: %{customdata}<br>"
            + "<extra></extra>",
            customdata=chunk_hover_texts,
            name="Similarity Scores",
        )
    )

    # Update layout
    fig.update_layout(
        title=dict(
            text=f"{title}<br>Query: {query[:50]}{'...' if len(query) > 50 else ''}",
            x=0.5,
            font=dict(size=14),
        ),
        xaxis_title="Chunks",
        yaxis_title="Cosine Similarity Score",
        xaxis=dict(tickangle=45),
        yaxis=dict(range=[0, max(similarities) * 1.1]),
        width=1000,
        height=600,
        hovermode="x",
        showlegend=False,
    )

    # Add a horizontal line at similarity threshold (e.g., 0.5)
    fig.add_hline(
        y=0.5,
        line_dash="dash",
        line_color="gray",
        annotation_text="Relevance Threshold (0.5)",
        annotation_position="top right",
    )

    print("1D similarity visualization created successfully!")

    return fig


def visualize_embeddings_tsne(
    chunks,
    chunk_embeddings,
    query,
    query_embedding,
    perplexity=30,
    random_state=42,
    title="Embedding Visualization",
):
    """
    Visualize embeddings using t-SNE with Plotly.

    Args:
        chunks: List of text chunks
        chunk_embeddings: Numpy array of chunk embeddings
        query: Query text string
        query_embedding: Numpy array of query embedding (should be 1D or 2D with shape (1, embedding_dim))
        perplexity: t-SNE perplexity parameter (default: 30)
        random_state: Random state for reproducibility (default: 42)
        title: Title for the plot (default: "Embedding Visualization")

    Returns:
        plotly.graph_objects.Figure: Interactive plot figure
    """
    # Ensure query_embedding is 2D
    if query_embedding.ndim == 1:
        query_embedding = query_embedding.reshape(1, -1)

    # Combine chunk and query embeddings
    all_embeddings = np.vstack([chunk_embeddings, query_embedding])

    # Create labels for chunks and query
    chunk_labels = [f"Chunk {i+1}" for i in range(len(chunks))]
    query_label = ["Query"]
    all_labels = chunk_labels + query_label

    # Create hover text (first 50 characters of each chunk + query)
    chunk_hover_texts = [
        chunk[:50] + "..." if len(chunk) > 50 else chunk for chunk in chunks
    ]
    query_hover_text = [query[:50] + "..." if len(query) > 50 else query]
    all_hover_texts = chunk_hover_texts + query_hover_text

    # Create colors (chunks in blue, query in red)
    chunk_colors = ["Chunk"] * len(chunks)
    query_color = ["Query"]
    all_colors = chunk_colors + query_color

    # Apply t-SNE
    print(f"Applying t-SNE to {len(all_embeddings)} embeddings...")
    tsne = TSNE(
        n_components=2,
        perplexity=min(perplexity, len(all_embeddings) - 1),
        random_state=random_state,
        init="random",
    )
    embeddings_2d = tsne.fit_transform(all_embeddings)

    # Create the plot
    fig = go.Figure()

    # Add chunks
    chunk_x = embeddings_2d[:-1, 0]  # All except last (query)
    chunk_y = embeddings_2d[:-1, 1]

    fig.add_trace(
        go.Scatter(
            x=chunk_x,
            y=chunk_y,
            mode="markers",
            marker=dict(
                size=8, color="lightblue", line=dict(width=1, color="darkblue")
            ),
            text=chunk_hover_texts,
            hovertemplate="<b>%{text}</b><br>X: %{x:.2f}<br>Y: %{y:.2f}<extra></extra>",
            name="Chunks",
            showlegend=True,
        )
    )

    # Add query
    query_x = embeddings_2d[-1, 0]  # Last point (query)
    query_y = embeddings_2d[-1, 1]

    fig.add_trace(
        go.Scatter(
            x=[query_x],
            y=[query_y],
            mode="markers",
            marker=dict(
                size=12, color="red", symbol="star", line=dict(width=2, color="darkred")
            ),
            text=query_hover_text,
            hovertemplate="<b>Query:</b> %{text}<br>X: %{x:.2f}<br>Y: %{y:.2f}<extra></extra>",
            name="Query",
            showlegend=True,
        )
    )

    # Update layout
    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=16)),
        xaxis_title="t-SNE Dimension 1",
        yaxis_title="t-SNE Dimension 2",
        width=800,
        height=600,
        hovermode="closest",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    )

    print("t-SNE visualization created successfully!")
    return fig


if __name__ == "__main__":
    ### Task 1: YOUR CODE HERE - Write a prompt for the LLM to respond to the user
    prompt = "what are the tourist attractions in morocco?"

    # Get Response
    response = prompt_llm(prompt)

    print("\nResponse:\n")
    print(response)
    print("-" * 100)

    # save response under results/
    with open("results/response.txt", "w") as f:
        f.write(response)
