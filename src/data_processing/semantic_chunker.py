import re
import jieba
from typing import List, Dict

class ZJUHistoryChunker:
    def __init__(self):
        self.zju_terms = self.load_zju_terminology()
        
    def load_zju_terminology(self):
        terms = [
            "求是书院", "国立浙江大学", "浙大西迁", "文军长征", "东方剑桥",
            "竺可桢", "林启", "蒋梦麟", "四校合并", "院系调整"
        ]
        for term in terms:
            jieba.add_word(term)
        return terms
    
    def identify_sections(self, text: str) -> List[Dict]:
        sections = []
        print(f"文档总长度: {len(text)} 字符")
        section_patterns = [
            r'\n\s*([^。！？\n]+?（\d{4}-\d{4}）)\s*\n',
            r'\n\s*([^。！？\n]{2,20}?)\s*\n(?![\s\S]*[。！？])',
            r'\n\s*([初二三四]迁[^。！？\n]+)\s*\n',
        ]
        all_matches = []
        for pattern in section_patterns:
            matches = list(re.finditer(pattern, text))
            for match in matches:
                all_matches.append({
                    'start': match.start(),
                    'end': match.end(),
                    'title': match.group(1).strip(),
                    'pattern': pattern
                })
        all_matches.sort(key=lambda x: x['start'])
        print(f"找到 {len(all_matches)} 个可能的章节标题")
        for match in all_matches:
            print(f"  标题: '{match['title']}' (位置: {match['start']})")
        if not all_matches:
            print("未找到章节标题，将整个文档作为一个章节")
            sections.append({
                "level": 1,
                "title": "全文",
                "content": text,
                "start_pos": 0,
                "end_pos": len(text)
            })
            return sections
        for i, match in enumerate(all_matches):
            start_pos = match['end']
            end_pos = all_matches[i+1]['start'] if i < len(all_matches) - 1 else len(text)
            content = text[start_pos:end_pos].strip()
            level = 2 if '迁' in match['title'] else 1
            sections.append({
                "level": level,
                "title": match['title'],
                "content": content,
                "start_pos": start_pos,
                "end_pos": end_pos
            })
        return sections
    
    def robust_chunking(self, content: str, max_chunk_size: int = 400) -> List[Dict]:
        if not content or len(content.strip()) == 0:
            return []
        chunks = []
        sentence_delimiters = r'[。！？!?]'
        sentences = re.split(sentence_delimiters, content)
        sentences = [s.strip() for s in sentences if s.strip()]
        current_chunk = ""
        for sentence in sentences:
            if current_chunk and len(current_chunk) + len(sentence) > max_chunk_size:
                chunks.append({
                    "content": current_chunk.strip(),
                    "time_period": self.extract_time_period(current_chunk),
                    "type": "content_chunk"
                })
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += "。" + sentence
                else:
                    current_chunk = sentence
        if current_chunk:
            chunks.append({
                "content": current_chunk.strip(),
                "time_period": self.extract_time_period(current_chunk),
                "type": "content_chunk"
            })
        if not chunks and len(content) > 0:
            print("使用固定长度分块")
            chunk_size = min(max_chunk_size, len(content))
            for i in range(0, len(content), chunk_size):
                chunk_content = content[i:i+chunk_size].strip()
                if chunk_content:
                    chunks.append({
                        "content": chunk_content,
                        "time_period": self.extract_time_period(chunk_content),
                        "type": "fixed_length_chunk"
                    })
        return chunks
    
    def extract_time_period(self, text: str) -> str:
        time_patterns = [
            r'(\d{4})年',
            r'(\d{4}-\d{4})年',
        ]
        for pattern in time_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        return ""
    
    def chunk_by_timeline(self, content: str, max_chunk_size: int = 400) -> List[Dict]:
        return self.robust_chunking(content, max_chunk_size)
