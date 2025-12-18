import json
from vector_db import SimpleVectorDB
from data_processing.metadata_extractor import MetadataExtractor

def rebuild_vector_database():
    print("[INFO] 开始重建向量数据库（使用优化数据）...")
    try:
        with open("processed_data/optimized_chunks.json", "r", encoding="utf-8") as f:
            optimized_chunks = json.load(f)
    except FileNotFoundError:
        print("[ERROR] 优化数据文件不存在，请先运行 document_cleaner.py")
        return
    print(f"[INFO] 加载了 {len(optimized_chunks)} 个优化文本块")
    metadata_extractor = MetadataExtractor()
    documents = []
    for chunk in optimized_chunks:
        metadata = metadata_extractor.extract_from_content(chunk['content'])
        if 'figures' in chunk:
            metadata['persons'] = list(set(metadata['persons'] + chunk['figures']))
        if 'locations' in chunk:
            metadata['locations'] = list(set(metadata['locations'] + chunk['locations']))
        if 'time_periods' in chunk:
            metadata['time_periods'] = list(set(metadata['time_periods'] + chunk['time_periods']))
        document = {
            "id": chunk['id'],
            "content": chunk['content'],
            "section_title": f"{chunk.get('filename', '文档')} - {chunk.get('source', '内容')}",
            "section_level": 1,
            "time_period": chunk.get('time_periods', [''])[0] if chunk.get('time_periods') else "",
            "chunk_type": "optimized_chunk",
            "metadata": metadata,
            "source": chunk.get('source', '优化文档'),
            "quality_score": chunk.get('quality_score', 0.5),
            "word_count": chunk.get('word_count', 0),
            "process_time": chunk.get('chunk_timestamp', '')
        }
        documents.append(document)
    print(f"[INFO] 准备向量的数据库添加 {len(documents)} 个优化文档")
    documents.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
    vector_db = SimpleVectorDB()
    vector_db.add_documents(documents)
    print("[SUCCESS] 向量数据库重建完成！")

if __name__ == "__main__":
    rebuild_vector_database()
