import chromadb
import os

CHROMA_API_KEY= os.getenv("CHROMA_API_KEY")

if CHROMA_API_KEY:
    client = chromadb.CloudClient(
        api_key=CHROMA_API_KEY,
        tenant=os.getenv("CHROMA_TENANT"),
        database=os.getenv("CHROMA_DATABASE"),
    )
else:
    client = chromadb.HttpClient(host=os.getenv("CHROMA_HOST", "localhost"), port=int(os.getenv("CHROMA_PORT", "8001")))

collection = client.get_or_create_collection(name="memmories")

def add_embedding(memmory_id: str, vector: list[dict], text: str, user_id: str):
    """Store a memory's vector, indexed by its memory_id, tagged with the owning user"""
    collection.add(
        ids=[memmory_id],
        embeddings=[vector],
        documents=[text],
        metadatas=[{"user_id": user_id}],
    )

def find_similar(vector: list[float], user_id: str, top_k: int = 3) -> list[dict]:
    """Find the closest existing memories to a given vector, scoped to one user"""
    results = collection.query(
        query_embeddings=[vector],
        n_results=top_k,
        where={"user_id": user_id},
    )
    
    matches=[]
    if results["ids"] and results["ids"][0]:
        for i in range(len(results["ids"][0])):
            matches.append({
                "memory_id":results["ids"][0][i],
                "text":results["documents"][0][i],
                "distance":results["distances"][0][i],
            })
    return matches