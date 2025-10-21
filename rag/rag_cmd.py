import os
from rag_utils import (
    load_data,
    get_chunks,
    get_embeddings,
    retrieve_closest_chunk,
    get_rag_with_chunk,
    visualize_embeddings_tsne,
    visualize_embeddings_1d,
    load_html_page,
)


if __name__ == "__main__":
    base_path = "/Users/yunustuncbilek/Desktop/workshopAI/math-mate/rag/data"

    # Set your question here
    user_question = "Which lecture is most relevant to this HW: Problem 2: The integral $\\int \\frac{x^2 + 1}{x(x^2+4)} \\, dx$ is to be evaluated."

    print("\n" + "=" * 80)
    print("## USER QUESTION")
    print("-" * 80)
    print(f"Question: {user_question}")
    print("Searching for relevant information...")
    print("\n")

    # Load Health Gateway BC website
    healthbc_website = load_html_page(
        url="https://en.wikipedia.org/wiki/HealthLinkBC",
        output_file=f"{base_path}/healthbc.txt",
    )
    fname = "lectures.txt"

    # LOAD AND PROCESS DATA
    # ----------------------
    data_file = f"{base_path}/{fname}"
    data_txt = load_data(data_file)
    os.makedirs(f"{base_path}", exist_ok=True)
    chunks = get_chunks(data_txt, save_to=f"{base_path}/chunks.json")
    embeddings = get_embeddings(chunks, save_to=f"{base_path}/dataembeddings.pkl")

    # RETRIEVE CLOSEST CHUNK
    # -----------------------
    closest_chunk, similarity, chunk_idx, query_embedding, all_similarities = (
        retrieve_closest_chunk(user_question, chunks, embeddings)
    )

    # save closest chunk to file
    with open(f"{base_path}/closest_chunk.txt", "w") as f:
        f.write(closest_chunk)

    print("\n" + "=" * 80)
    print("## SIMILARITY SCORES")
    print("-" * 80)

    # COMPUTE SIMILARITY SCORES
    # -------------------------
    print("Similarity between query and every chunk:")
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i} (similarity: {all_similarities[i]:.3f}): {chunk[:50]}... \n")

    # GENERATE RAG RESPONSE
    # ---------------------
    rag_output, chunk_content, chunk_index = get_rag_with_chunk(
        user_question, closest_chunk, chunk_idx, save_to=f"{base_path}"
    )

    print("\n" + "=" * 80)
    print("## RAG RESPONSE")
    print("-" * 80)
    print(f"Response:\n{rag_output}")
    print(f"Source: Chunk {chunk_index} (similarity: {similarity:.3f})")
    print(f"Chunk Content: {chunk_content[:20]}...")

    # SHOW 1D SIMILARITY VISUALIZATION IN PLOTLY OF THE EMBEDDINGS BETWEEN THE QUERY AND THE CHUNKS
    # ------------------------------------------------------------------------------------------------
    # Create and show the 1D similarity visualization
    fig = visualize_embeddings_1d(
        chunks=chunks,
        chunk_embeddings=embeddings,
        query=user_question,
        query_embedding=query_embedding,
        title="Patient Data Embeddings Visualization",
    )

    fig.write_html(f"{base_path}/1d_similarity_visualization.html")
    # VISUALIZATION
    # --------------

    # print("\n" + "=" * 80)
    # print("## VISUALIZATION")
    # print("-" * 80)
    # # Create and show the t-SNE visualization
    # print("Creating t-SNE visualization...")
    # fig = visualize_embeddings_tsne(
    #     chunks=chunks,
    #     chunk_embeddings=embeddings,
    #     query=user_question,
    #     query_embedding=query_embedding,
    #     title="Patient Data Embeddings Visualization",
    # )

    # # Optionally save the plot as HTML
    # fig.write_html(f"{base_path}/embeddings_visualization.html")
    # print("Visualization saved as 'rag/embeddings_visualization.html'")
    # print("=" * 80)
