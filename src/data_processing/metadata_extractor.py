import re
from typing import Dict

class MetadataExtractor:
    def __init__(self):
        self.time_periods = self.load_time_periods()
        self.important_figures = self.load_important_figures()
        self.locations = self.load_locations()
    
    def load_time_periods(self):
        return {
            "溯源求是": ("1897", "1928"),
            "探求崛起": ("1928", "1952"), 
            "调整发展": ("1952", "1998"),
            "争创一流": ("1998", "2024")
        }
    
    def load_important_figures(self):
        return [
            "林启", "竺可桢", "蒋梦麟", "陈建功", "苏步青", "束星北", 
            "贝时璋", "蔡邦华", "马一浮", "丰子恺", "钱穆", "王淦昌",
            "谈家桢", "李政道", "程开甲", "谷超豪", "叶笃正"
        ]
    
    def load_locations(self):
        return [
            "杭州", "建德", "吉安", "泰和", "宜山", "遵义", "湄潭",
            "天目山", "禅源寺", "紫金港", "玉泉", "之江", "华家池"
        ]
    
    def extract_from_content(self, content: str) -> Dict:
        metadata = {
            "time_periods": [],
            "persons": [],
            "locations": [],
            "events": [],
            "institutions": []
        }
        
        for period, (start, end) in self.time_periods.items():
            if period in content:
                metadata["time_periods"].append(period)
        
        years = re.findall(r'\d{4}年', content)
        metadata["time_periods"].extend(years)
        
        for person in self.important_figures:
            if person in content:
                metadata["persons"].append(person)
        
        for location in self.locations:
            if location in content:
                metadata["locations"].append(location)
        
        event_keywords = ["创立", "成立", "迁往", "调整", "合并", "西迁", "办学"]
        sentences = re.split(r'[。！？]', content)
        for sentence in sentences:
            if any(keyword in sentence for keyword in event_keywords):
                metadata["events"].append(sentence.strip())
        
        institutions = re.findall(r'[《]?(浙江大学|求是书院|杭州大学|浙江农业大学|浙江医科大学)[》]?', content)
        metadata["institutions"].extend(institutions)
        
        for key in metadata:
            metadata[key] = list(set(metadata[key]))
        
        return metadata
