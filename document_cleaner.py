import re
import json
import os
from typing import List, Dict, Tuple
from datetime import datetime

class ZJUDocumentCleaner:
    def __init__(self):
        self.cleaned_documents = []
        
    def clean_all_documents(self):
        """清洗所有文档"""
        documents_info = [
            ("zju_history.txt", "校史概述"),
            ("zju_history_baidu.txt", "百度百科"), 
            ("zju_history_wiki.txt", "维基百科")
        ]
        
        for filename, source in documents_info:
            print(f"🧹 正在清洗: {filename}")
            cleaned_content = self.clean_single_document(filename, source)
            if cleaned_content:
                self.cleaned_documents.append(cleaned_content)
        
        # 保存清洗后的文档
        self.save_cleaned_documents()
        return self.cleaned_documents
    
    def clean_single_document(self, filename: str, source: str) -> Dict:
        """清洗单个文档"""
        filepath = f"raw_data/documents/{filename}"
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            print(f"  原始长度: {len(content)} 字符")
            
            # 分步骤清洗
            content = self.remove_reference_marks(content)  # 移除引用标记
            content = self.clean_formatting(content)        # 清理格式
            content = self.normalize_dates(content)         # 标准化日期
            content = self.split_long_paragraphs(content)   # 分割长段落
            content = self.remove_redundant_info(content)   # 移除冗余信息
            
            # 结构化处理
            structured_content = self.structure_content(content, filename)
            
            print(f"  清洗后: {len(content)} 字符")
            
            return {
                "filename": filename,
                "source": source,
                "original_length": len(content),
                "cleaned_length": len(structured_content.get('content', '')),
                "content": structured_content.get('content', ''),
                "paragraphs": structured_content.get('paragraphs', []),
                "time_periods": structured_content.get('time_periods', []),
                "key_figures": structured_content.get('key_figures', []),
                "key_locations": structured_content.get('key_locations', []),
                "cleaned_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            print(f"❌ 清洗文件 {filename} 失败: {e}")
            return None
    
    def remove_reference_marks(self, content: str) -> str:
        """移除引用标记和注释"""
        # 移除 [数字] 格式的引用标记
        content = re.sub(r'\[\d+\]', '', content)
        # 移除 [需要解释] 等注释
        content = re.sub(r'\[[^\]]*?\]', '', content)
        # 移除 (主词条：...) 等说明
        content = re.sub(r'（主词条：[^）]*?）', '', content)
        return content
    
    def clean_formatting(self, content: str) -> str:
        """清理格式"""
        # 统一换行符
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # 移除多余的空行和空白字符
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        # 重新组合，确保段落之间有适当的间距
        cleaned_lines = []
        for i, line in enumerate(lines):
            # 如果当前行是标题格式（短文本且没有句号），单独成段
            if len(line) < 50 and '。' not in line and i < len(lines)-1:
                cleaned_lines.append(line)
                cleaned_lines.append('')  # 空行分隔
            else:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def normalize_dates(self, content: str) -> str:
        """标准化日期格式"""
        # 统一年份表示
        content = re.sub(r'(\d{4})—(\d{4})', r'\1-\2', content)  # 替换全角破折号
        content = re.sub(r'(\d{4})-(\d{4})', r'\1至\2', content)  # 统一为"至"
        
        # 标准化时间范围
        content = re.sub(r'（(\d{4})-(\d{4})）', r'（\1至\2）', content)
        
        return content
    
    def split_long_paragraphs(self, content: str) -> str:
        """分割过长的段落"""
        paragraphs = content.split('\n\n')
        result_paragraphs = []
        
        for para in paragraphs:
            if len(para) > 500:  # 如果段落超过500字，进行分割
                # 按句子分割
                sentences = re.split(r'[。！？]', para)
                sentences = [s.strip() for s in sentences if s.strip()]
                
                current_chunk = []
                current_length = 0
                
                for sentence in sentences:
                    if current_length + len(sentence) > 300 and current_chunk:
                        # 保存当前块
                        result_paragraphs.append('。'.join(current_chunk) + '。')
                        current_chunk = [sentence]
                        current_length = len(sentence)
                    else:
                        current_chunk.append(sentence)
                        current_length += len(sentence)
                
                if current_chunk:
                    result_paragraphs.append('。'.join(current_chunk) + '。')
            else:
                result_paragraphs.append(para)
        
        return '\n\n'.join(result_paragraphs)
    
    def remove_redundant_info(self, content: str) -> str:
        """移除冗余信息"""
        # 移除过于详细的院系调整列表（保留概括性描述）
        lines = content.split('\n')
        cleaned_lines = []
        skip_next = False
        
        for i, line in enumerate(lines):
            # 跳过过于详细的列表项
            if '理学院数学系、物理系、化学系、生物系分别并入' in line:
                # 保留概括，跳过详细列表
                cleaned_lines.append("理学院各系分别调整至复旦大学、上海第一医学院、华东师范大学、南京大学等相关院校。")
                skip_next = True
            elif skip_next and (line.startswith('　　') or not line.strip()):
                continue
            elif '浙江大学院系调整状况如下' in line:
                skip_next = True
                continue
            elif skip_next and not line.startswith('　　'):
                skip_next = False
                if line.strip():
                    cleaned_lines.append(line)
            else:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def structure_content(self, content: str, filename: str) -> Dict:
        """将内容结构化"""
        # 按空行分割段落
        raw_paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        structured_paragraphs = []
        all_time_periods = []
        all_figures = []
        all_locations = []
        
        for para in raw_paragraphs:
            if len(para) < 10:  # 跳过过短的段落
                continue
                
            # 提取时间信息
            time_periods = self.extract_time_periods(para)
            all_time_periods.extend(time_periods)
            
            # 提取人物
            figures = self.extract_figures(para)
            all_figures.extend(figures)
            
            # 提取地点
            locations = self.extract_locations(para)
            all_locations.extend(locations)
            
            # 为段落添加结构信息
            structured_para = {
                "content": para,
                "length": len(para),
                "time_periods": time_periods,
                "figures": figures,
                "locations": locations,
                "has_timeline": bool(time_periods)
            }
            structured_paragraphs.append(structured_para)
        
        # 构建最终内容（合并所有段落）
        final_content = '\n\n'.join([p["content"] for p in structured_paragraphs])
        
        return {
            "content": final_content,
            "paragraphs": structured_paragraphs,
            "time_periods": list(set(all_time_periods)),
            "key_figures": list(set(all_figures)),
            "key_locations": list(set(all_locations))
        }
    
    def extract_time_periods(self, text: str) -> List[str]:
        """提取时间信息"""
        patterns = [
            r'\d{4}年',                    # 1949年
            r'\d{4}至\d{4}年',             # 1937至1945年
            r'\d{4}-\d{4}',                # 1897-1928
            r'（\d{4}至\d{4}）',           # （1897至1928）
        ]
        
        time_periods = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            time_periods.extend(matches)
        
        return time_periods
    
    def extract_figures(self, text: str) -> List[str]:
        """提取人物"""
        figures = [
            "竺可桢", "林启", "蒋梦麟", "陈建功", "苏步青", "束星北", 
            "贝时璋", "蔡邦华", "马一浮", "丰子恺", "钱穆", "王淦昌",
            "谈家桢", "李政道", "程开甲", "谷超豪", "叶笃正", "李约瑟",
            "邵飘萍", "何燏时", "蒋方震", "费巩", "于子三", "马寅初",
            "刘丹", "路甬祥", "张其昀", "郑晓沧", "邵裴子", "郭任远"
        ]
        
        return [f for f in figures if f in text]
    
    def extract_locations(self, text: str) -> List[str]:
        """提取地点"""
        locations = [
            "杭州", "建德", "吉安", "泰和", "宜山", "遵义", "湄潭",
            "天目山", "禅源寺", "紫金港", "玉泉", "之江", "华家池",
            "龙泉", "松木场", "湖滨", "舟山", "海宁", "宁波", "上海",
            "南京", "北京", "贵州", "江西", "广西", "浙江"
        ]
        
        return [l for l in locations if l in text]
    
    def save_cleaned_documents(self):
        """保存清洗后的文档"""
        # 保存清洗后的完整文档
        for doc in self.cleaned_documents:
            filename = f"cleaned_{doc['filename']}"
            filepath = f"raw_data/documents/{filename}"
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(doc['content'])
        
        # 保存清洗元数据
        metadata = {
            "cleaned_documents": self.cleaned_documents,
            "total_documents": len(self.cleaned_documents),
            "total_paragraphs": sum(len(doc.get('paragraphs', [])) for doc in self.cleaned_documents),
            "total_figures": len(set(f for doc in self.cleaned_documents for f in doc.get('key_figures', []))),
            "total_locations": len(set(l for doc in self.cleaned_documents for l in doc.get('key_locations', []))),
            "cleaning_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open("processed_data/cleaning_metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 清洗完成！生成文件:")
        for doc in self.cleaned_documents:
            print(f"   - cleaned_{doc['filename']}")
        print("   - processed_data/cleaning_metadata.json")

class OptimizedChunker:
    """优化后的分块器，专门针对清洗后的文档"""
    
    def __init__(self, max_chunk_size=350, overlap=30):
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
    
    def chunk_cleaned_documents(self, cleaned_documents: List[Dict]) -> List[Dict]:
        """对清洗后的文档进行智能分块"""
        all_chunks = []
        
        for doc in cleaned_documents:
            print(f"📄 处理文档: {doc['filename']}")
            doc_chunks = self.chunk_single_document(doc)
            all_chunks.extend(doc_chunks)
        
        print(f"✅ 分块完成，共生成 {len(all_chunks)} 个优化文本块")
        return all_chunks
    
    def chunk_single_document(self, document: Dict) -> List[Dict]:
        """处理单个文档"""
        chunks = []
        paragraphs = document.get('paragraphs', [])
        
        for i, para in enumerate(paragraphs):
            content = para['content']
            
            # 如果段落长度合适，直接作为一个块
            if len(content) <= self.max_chunk_size:
                chunk = self.create_chunk(document, content, i)
                chunks.append(chunk)
            else:
                # 需要进一步分割
                sub_chunks = self.split_paragraph(content, document, i)
                chunks.extend(sub_chunks)
        
        return chunks
    
    def split_paragraph(self, paragraph: str, document: Dict, para_index: int) -> List[Dict]:
        """分割长段落"""
        # 按句子分割，保留句子完整性
        sentences = re.split(r'[。！？]', paragraph)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_with_punct = sentence + '。'
            
            if current_length + len(sentence_with_punct) > self.max_chunk_size and current_chunk:
                # 保存当前块
                chunk_content = ''.join(current_chunk)
                chunk = self.create_chunk(document, chunk_content, para_index, len(chunks))
                chunks.append(chunk)
                
                # 保留重叠部分以保持上下文
                overlap_sentences = current_chunk[-2:] if len(current_chunk) > 2 else current_chunk[-1:]
                current_chunk = overlap_sentences + [sentence_with_punct]
                current_length = sum(len(s) for s in current_chunk)
            else:
                current_chunk.append(sentence_with_punct)
                current_length += len(sentence_with_punct)
        
        # 处理最后一个块
        if current_chunk:
            chunk_content = ''.join(current_chunk)
            chunk = self.create_chunk(document, chunk_content, para_index, len(chunks))
            chunks.append(chunk)
        
        return chunks
    
    def create_chunk(self, document: Dict, content: str, para_index: int, sub_index: int = None) -> Dict:
        """创建优化后的数据块"""
        chunk_id = f"{document['filename'].replace('.txt', '')}_p{para_index}"
        if sub_index is not None:
            chunk_id += f"_s{sub_index}"
        
        # 为每个块提取独立的元数据
        time_periods = self.extract_time_periods(content)
        figures = self.extract_figures(content)
        locations = self.extract_locations(content)
        
        return {
            "id": chunk_id,
            "content": content,
            "source": document['source'],
            "filename": document['filename'],
            "word_count": len(content),
            "time_periods": time_periods,
            "figures": figures,
            "locations": locations,
            "chunk_type": "optimized_chunk",
            "quality_score": self.assess_chunk_quality(content, time_periods, figures),
            "chunk_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def extract_time_periods(self, content: str) -> List[str]:
        """提取时间信息"""
        return re.findall(r'\d{4}年|\d{4}至\d{4}年', content)
    
    def extract_figures(self, content: str) -> List[str]:
        """提取人物"""
        figures = ["竺可桢", "林启", "蒋梦麟", "陈建功", "苏步青", "束星北", 
                  "贝时璋", "蔡邦华", "马一浮", "丰子恺", "钱穆", "王淦昌"]
        return [f for f in figures if f in content]
    
    def extract_locations(self, content: str) -> List[str]:
        """提取地点"""
        locations = ["杭州", "建德", "吉安", "泰和", "宜山", "遵义", "湄潭"]
        return [l for l in locations if l in content]
    
    def assess_chunk_quality(self, content: str, time_periods: List, figures: List) -> float:
        """评估块质量"""
        score = 0.0
        
        # 长度适中得分
        if 100 <= len(content) <= 400:
            score += 0.3
        elif len(content) > 400:
            score += 0.1
        
        # 有时间信息得分
        if time_periods:
            score += 0.3
        
        # 有人物信息得分
        if figures:
            score += 0.2
        
        # 有地点信息得分
        if self.extract_locations(content):
            score += 0.2
        
        return min(score, 1.0)

def main():
    """主函数：执行完整的文档清洗和优化流程"""
    print("🚀 开始浙大校史文档深度清洗与优化...")
    
    # 1. 文档清洗
    print("\n🧹 阶段1: 文档深度清洗")
    cleaner = ZJUDocumentCleaner()
    cleaned_docs = cleaner.clean_all_documents()
    
    if not cleaned_docs:
        print("❌ 文档清洗失败")
        return
    
    # 2. 优化分块
    print("\n✂️ 阶段2: 优化分块")
    chunker = OptimizedChunker()
    optimized_chunks = chunker.chunk_cleaned_documents(cleaned_docs)
    
    # 3. 保存优化后的数据
    print("\n💾 阶段3: 保存数据")
    os.makedirs("processed_data", exist_ok=True)
    
    # 保存优化分块
    with open("processed_data/optimized_chunks.json", "w", encoding="utf-8") as f:
        json.dump(optimized_chunks, f, ensure_ascii=False, indent=2)
    
    # 4. 统计信息
    total_words = sum(chunk['word_count'] for chunk in optimized_chunks)
    avg_chunk_size = total_words / len(optimized_chunks) if optimized_chunks else 0
    high_quality_chunks = sum(1 for c in optimized_chunks if c.get('quality_score', 0) > 0.7)
    
    print(f"""
🎉 文档清洗与优化完成！

📊 优化结果统计:
├── 清洗文档: {len(cleaned_docs)} 个
├── 优化文本块: {len(optimized_chunks)} 个
├── 总字数: {total_words} 字
├── 平均块大小: {avg_chunk_size:.1f} 字
├── 高质量块: {high_quality_chunks} 个 (质量分>0.7)
└── 平均质量分: {sum(c.get('quality_score', 0) for c in optimized_chunks) / len(optimized_chunks):.2f}

💾 生成文件:
├── raw_data/documents/cleaned_*.txt (清洗后的文档)
├── processed_data/cleaning_metadata.json (清洗元数据)
└── processed_data/optimized_chunks.json (优化分块数据)

🎯 接下来运行: python rebuild_vector_db.py
    """)

if __name__ == "__main__":
    main()