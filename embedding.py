from sentence_transformers import SentenceTransformer


# Load the embedding model
model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


def create_embedding(text):

    embedding = model.encode(
        text,
        normalize_embeddings=True
    )

    return embedding.tolist()
if __name__ == "__main__":

    text = """
    AWS GST Invoice Available
    Amazon Web Services
    Download the GST invoice from the AWS Billing console.
    """

    vector = create_embedding(text)

    print("Embedding created!")
    print("Vector dimensions:", len(vector))
    print("First 10 values:", vector[:10])