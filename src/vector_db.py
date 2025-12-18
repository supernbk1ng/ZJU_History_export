import os
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any

class SimpleVectorDB:
    def __init__(self, db_path="./chroma_db", collection_name="zju_history"):
        self.db_path = db_path
        self.collection_name = collection_name
        print("Connecting to ChromaDB...")
        self.client = chromadb.PersistentClient(path=db_path)
        print("Using DefaultEmbeddingFunction (all-MiniLM-L6-v2)...")
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn
        )

    def add_documents(self, documents: List[Dict[str, Any]]):
        if not documents:
            print("[WARN] No documents to add")
            return
        print(f"Processing {len(documents)} documents for ChromaDB...")
        ids = []
        contents = []
        metadatas = []
        for doc in documents:
            doc_id = doc.get('id')
            if not doc_id:
                doc_id = f"doc_{len(ids)+1}"
            ids.append(str(doc_id))
            contents.append(str(doc.get('content', '')))
            metadata = doc.get('metadata', {})
            clean_meta = {}
            for k, v in metadata.items():
                if v is None:
                    continue
                clean_meta[k] = str(v) if not isinstance(v, (list, dict)) else v
            if 'id' in doc and 'id' not in clean_meta:
                clean_meta['original_id'] = doc['id']
            metadatas.append(clean_meta)
        if len(metadatas) > 0:
            print(f"Debug: First metadata sample: {metadatas[0]}")
        try:
            self.collection.upsert(documents=contents, metadatas=metadatas, ids=ids)
            print(f"[INFO] Successfully added/updated {len(documents)} documents in ChromaDB")
        except Exception as e:
            print(f"[ERROR] Failed to add documents in batch: {e}")
            print("[INFO] Retrying one by one...")
            success_count = 0
            for idx in range(len(ids)):
                try:
                    self.collection.upsert(
                        documents=[contents[idx]],
                        metadatas=[metadatas[idx]],
                        ids=[ids[idx]]
                    )
                    success_count += 1
                except Exception as inner_e:
                    print(f"Error adding doc {idx} (ID: {ids[idx]}): {inner_e}")
                    try:
                        self.collection.upsert(
                            documents=[contents[idx]],
                            metadatas=[{}],
                            ids=[ids[idx]]
                        )
                        print(f"  -> Added doc {idx} without metadata.")
                        success_count += 1
                    except:
                        print(f"  -> Failed to add doc {idx} even without metadata.")
            print(f"[INFO] Successfully added {success_count}/{len(documents)} documents one-by-one.")

    def query(self, query_text: str, n_results: int = 3) -> List[Dict]:
        if not query_text or not query_text.strip():
            print("[WARN] Empty query text")
            return []
        print(f"[INFO] Vector Query: '{query_text}'")
        try:
            print(f"Debug: calling collection.query with text='{query_text}' and n_results={n_results}")
            results = self.collection.query(query_texts=[query_text], n_results=n_results)
            print(f"Debug: collection.query returned keys: {results.keys()}")
            formatted_results = []
            if not results['ids'] or len(results['ids'][0]) == 0:
                return []
            for i in range(len(results['ids'][0])):
                distance = results['distances'][0][i]
                similarity = 1 / (1 + distance)
                formatted_results.append({
                    'document': {
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'id': results['ids'][0][i]
                    },
                    'similarity': similarity,
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i]
                })
            print(f"[INFO] Found {len(formatted_results)} results")
            return formatted_results
        except Exception as e:
            print(f"[ERROR] Query failed: {e}")
            return []

    def load_data(self):
        count = self.collection.count()
        if count > 0:
            print(f"[INFO] ChromaDB collection '{self.collection_name}' has {count} documents.")
            return True
        else:
            print(f"[WARN] ChromaDB collection '{self.collection_name}' is empty.")
            return False
