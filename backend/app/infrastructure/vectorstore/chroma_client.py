import chromadb

client = chromadb.HttpClient(host="localhost", port=8001)

collection = client.get_or_create_collection(name="memmories")

def add_embedding(memmory_id:str,vector:list[dict],text:str):
    """Store a memory'vector,indexed by its memory_id"""
    collection.add(
        ids=[memmory_id],
        embeddings=[vector],
        documents=[text],
    )
    
def find_similar(vector:list[float],top_k:int=3) -> list[dict]:
    """Find the closest existing memories to a given vector"""
    results = collection.query(
        query_embeddings=[vector],
        n_results=top_k,
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