import json
import os
import time
import re
from typing import List, Dict

class ZJUHistoryDataCollector:
    def __init__(self):
        self.data_dir = "raw_data/documents"
        
    def load_local_documents(self) -> List[Dict]:
        """加载本地文档资料"""
        documents = []
        
        # 定义要处理的文档
        local_files = {
            "zju_history.txt": "校史概述",
            "zju_history_baidu.txt": "百度百科资料", 
            "zju_history_wiki.txt": "维基百科资料"
        }
        
        for filename, doc_type in local_files.items():
            filepath = os.path.join(self.data_dir, filename)
            try:
                if os.path.exists(filepath):
                    print(f"📖 正在读取: {filename}")
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    if content.strip():
                        documents.append({
                            "type": doc_type,
                            "filename": filename,
                            "content": content,
                            "source": "本地文档",
                            "collected_time": time.strftime("%Y-%m-%d %H:%M:%S")
                        })
                        print(f"✅ 成功读取: {filename} ({len(content)} 字符)")
                    else:
                        print(f"⚠️ 文件为空: {filename}")
                else:
                    print(f"❌ 文件不存在: {filepath}")
                    
            except Exception as e:
                print(f"❌ 读取文件 {filename} 失败: {e}")
        
        print(f"📊 总共加载 {len(documents)} 个文档")
        return documents

class DataEnhancer:
    def __init__(self):
        self.enhanced_data = []
    
    def enhance_existing_data(self, raw_data: List[Dict]):
        """增强现有数据"""
        print("🔧 开始数据增强处理...")
        
        for item in raw_data:
            enhanced_item = self._enhance_single_item(item)
            self.enhanced_data.append(enhanced_item)
        
        print(f"✅ 数据增强完成，共处理 {len(self.enhanced_data)} 条数据")
        return self.enhanced_data
    
    def _enhance_single_item(self, item: Dict) -> Dict:
        """增强单个数据项"""
        content = item.get('content', '')
        
        # 数据清洗
        cleaned_content = self._clean_content(content)
        
        # 结构化处理
        structured_data = self._structure_content(cleaned_content)
        
        # 添加增强信息
        enhanced_item = {
            **item,
            "cleaned_content": cleaned_content,
            "structured_data": structured_data,
            "enhancement_level": self._assess_enhancement_level(cleaned_content),
            "word_count": len(cleaned_content),
            "key_topics": self._extract_key_topics(cleaned_content),
            "enhanced_time": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return enhanced_item
    
    def _clean_content(self, content: str) -> str:
        """清洗文本内容"""
        # 移除特殊字符但保留中文标点
        cleaned = re.sub(r'[^\u4e00-\u9fa5，。！？；：""''（）《》\s\w]', '', content)
        
        # 合并多个空白字符
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # 移除首尾空白
        cleaned = cleaned.strip()
        
        return cleaned
    
    def _structure_content(self, content: str) -> Dict:
        """将内容结构化"""
        # 按句子分割
        sentences = re.split(r'[。！？]', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # 识别段落
        paragraphs = []
        current_para = []
        
        for sentence in sentences:
            current_para.append(sentence)
            # 如果句子包含时间信息或达到一定长度，开始新段落
            if re.search(r'\d{4}年', sentence) or len(current_para) >= 3:
                if current_para:
                    paragraphs.append('。'.join(current_para) + '。')
                    current_para = []
        
        if current_para:
            paragraphs.append('。'.join(current_para) + '。')
        
        return {
            "sentences": sentences,
            "paragraphs": paragraphs,
            "time_periods": re.findall(r'\d{4}年', content),
            "key_figures": self._extract_figures(content),
            "locations": self._extract_locations(content)
        }
    
    def _extract_figures(self, content: str) -> List[str]:
        """提取人物姓名"""
        zju_figures = ["竺可桢", "林启", "蒋梦麟", "陈建功", "苏步青", "束星北", 
                      "贝时璋", "蔡邦华", "马一浮", "丰子恺", "钱穆", "王淦昌",
                      "谈家桢", "李政道", "程开甲", "谷超豪", "叶笃正", "李约瑟",
                      "邵飘萍", "何燏时", "蒋方震", "费巩", "于子三", "马寅初"]
        
        found_figures = []
        for figure in zju_figures:
            if figure in content:
                found_figures.append(figure)
        
        return found_figures
    
    def _extract_locations(self, content: str) -> List[str]:
        """提取地点"""
        zju_locations = ["杭州", "建德", "吉安", "泰和", "宜山", "遵义", "湄潭",
                        "天目山", "禅源寺", "紫金港", "玉泉", "之江", "华家池",
                        "龙泉", "松木场", "湖滨", "舟山", "海宁", "宁波"]
        
        found_locations = []
        for location in zju_locations:
            if location in content:
                found_locations.append(location)
        
        return found_locations
    
    def _extract_key_topics(self, content: str) -> List[str]:
        """提取关键主题"""
        topics = []
        
        key_themes = {
            "西迁": ["西迁", "迁校", "搬迁", "长征", "文军长征"],
            "合并": ["合并", "四校合并", "重组", "组建"],
            "创立": ["创立", "创建", "成立", "创办", "建立"],
            "发展": ["发展", "建设", "扩建", "壮大", "调整"],
            "成就": ["成就", "成果", "贡献", "获奖", "卓越"],
            "改革": ["改革", "改制", "调整", "改造"]
        }
        
        for theme, keywords in key_themes.items():
            if any(keyword in content for keyword in keywords):
                topics.append(theme)
        
        return topics
    
    def _assess_enhancement_level(self, content: str) -> str:
        """评估数据质量等级"""
        word_count = len(content)
        time_refs = len(re.findall(r'\d{4}年', content))
        figure_refs = len(self._extract_figures(content))
        
        if word_count > 800 and (time_refs > 3 or figure_refs > 2):
            return "高质量"
        elif word_count > 300:
            return "中等质量"
        else:
            return "基础质量"

class AdvancedChunker:
    def __init__(self):
        self.chunk_size = 400
        self.overlap = 50
    
    def chunk_enhanced_data(self, enhanced_data: List[Dict]) -> List[Dict]:
        """对增强数据进行智能分块"""
        chunks = []
        
        for item in enhanced_data:
            structured = item.get('structured_data', {})
            paragraphs = structured.get('paragraphs', [])
            
            for i, paragraph in enumerate(paragraphs):
                # 如果段落太长，进一步分割
                if len(paragraph) > self.chunk_size:
                    sub_chunks = self._split_long_paragraph(paragraph)
                    for j, sub_chunk in enumerate(sub_chunks):
                        chunk = self._create_chunk(item, sub_chunk, i, j)
                        chunks.append(chunk)
                else:
                    chunk = self._create_chunk(item, paragraph, i)
                    chunks.append(chunk)
        
        print(f"✅ 分块完成，共生成 {len(chunks)} 个文本块")
        return chunks
    
    def _split_long_paragraph(self, paragraph: str) -> List[str]:
        """分割长段落"""
        sentences = re.split(r'[。！？]', paragraph)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= self.chunk_size:
                if current_chunk:
                    current_chunk += "。" + sentence
                else:
                    current_chunk = sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk + "。")
                    current_chunk = sentence
                else:
                    # 单个句子就超过chunk_size，强制分割
                    chunks.append(sentence + "。")
                    current_chunk = ""
        
        if current_chunk:
            chunks.append(current_chunk + "。")
        
        return chunks
    
    def _create_chunk(self, item: Dict, content: str, para_index: int, sub_index: int = None) -> Dict:
        """创建标准化的数据块"""
        chunk_id = f"{item.get('filename', 'doc')}_p{para_index}"
        if sub_index is not None:
            chunk_id += f"_s{sub_index}"
        
        return {
            "id": chunk_id,
            "content": content,
            "source": item.get('source', '本地文档'),
            "filename": item.get('filename', 'unknown'),
            "original_type": item.get('type', 'unknown'),
            "enhancement_level": item.get('enhancement_level', 'unknown'),
            "key_topics": item.get('key_topics', []),
            "word_count": len(content),
            "time_periods": re.findall(r'\d{4}年', content),
            "figures": self._extract_figures_from_chunk(content),
            "locations": self._extract_locations_from_chunk(content),
            "chunk_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _extract_figures_from_chunk(self, content: str) -> List[str]:
        """从块中提取人物"""
        figures = ["竺可桢", "林启", "蒋梦麟", "陈建功", "苏步青", "束星北", 
                  "贝时璋", "蔡邦华", "马一浮", "丰子恺", "钱穆", "王淦昌",
                  "谈家桢", "李政道", "程开甲", "谷超豪", "叶笃正", "李约瑟"]
        
        return [f for f in figures if f in content]
    
    def _extract_locations_from_chunk(self, content: str) -> List[str]:
        """从块中提取地点"""
        locations = ["杭州", "建德", "吉安", "泰和", "宜山", "遵义", "湄潭",
                    "天目山", "禅源寺", "紫金港", "玉泉", "之江", "华家池"]
        
        return [l for l in locations if l in content]

def main():
    """主函数：执行完整的数据增强流程"""
    print("🚀 开始浙大校史数据增强流程...")
    
    # 1. 数据收集
    collector = ZJUHistoryDataCollector()
    print("📥 阶段1: 加载本地文档")
    local_data = collector.load_local_documents()
    
    if not local_data:
        print("❌ 没有找到可处理的文档，请检查 raw_data/documents/ 目录")
        return
    
    # 2. 数据增强
    print("🔧 阶段2: 数据增强")
    enhancer = DataEnhancer()
    enhanced_data = enhancer.enhance_existing_data(local_data)
    
    # 保存增强数据
    os.makedirs("processed_data", exist_ok=True)
    with open("processed_data/enhanced_raw_data.json", "w", encoding="utf-8") as f:
        json.dump(enhanced_data, f, ensure_ascii=False, indent=2)
    
    # 3. 智能分块
    print("✂️ 阶段3: 智能分块")
    chunker = AdvancedChunker()
    chunks = chunker.chunk_enhanced_data(enhanced_data)
    
    # 保存分块数据
    with open("processed_data/enhanced_chunks.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    
    # 4. 统计信息
    total_words = sum(chunk['word_count'] for chunk in chunks)
    total_figures = sum(len(chunk['figures']) for chunk in chunks)
    total_locations = sum(len(chunk['locations']) for chunk in chunks)
    avg_chunk_size = total_words / len(chunks) if chunks else 0
    
    print(f"""
🎉 数据增强完成！

📈 统计信息:
├── 原始文档: {len(local_data)} 个
├── 生成文本块: {len(chunks)} 个
├── 总字数: {total_words} 字
├── 涉及人物: {total_figures} 次
├── 涉及地点: {total_locations} 次
├── 平均块大小: {avg_chunk_size:.1f} 字
└── 高质量块: {sum(1 for c in chunks if c.get('enhancement_level') == '高质量')} 个

💾 输出文件:
├── processed_data/enhanced_raw_data.json (增强的原始数据)
└── processed_data/enhanced_chunks.json (智能分块数据)

接下来请运行: python rebuild_vector_db.py
    """)

if __name__ == "__main__":
    main()