import gradio as gr
import json
import re
import os
from datetime import datetime
from vector_db import SimpleVectorDB
from llm_client import LLMGenerator

class EnhancedZJUHistorySystem:
    def __init__(self):
        self.vector_db = SimpleVectorDB()
        self.llm = LLMGenerator()
        self.load_database()
        self.query_history = []

    def load_database(self):
        if not self.vector_db.load_data():
            print("请先构建向量数据库！")
            return False
        print("向量数据库加载成功！")
        return True

    def smart_query(self, question, top_k=3):
        if not question.strip():
            return "请输入问题", []
        keywords = self.extract_keywords(question)
        intent = self.understand_intent(question)
        print(f"[Query] Keywords: {keywords}, Intent: {intent}")
        results = self.vector_db.query(question, n_results=top_k)
        if not results and keywords:
            for keyword in keywords[:2]:
                results = self.vector_db.query(keyword, n_results=top_k)
                if results:
                    break
        self.query_history.append({
            "question": question,
            "time": datetime.now().isoformat(),
            "results_count": len(results) if results else 0
        })
        if not results:
            response = self.generate_no_results_response(question, keywords)
            yield response, []
            return
        for partial_response in self.generate_response(question, results, intent):
            yield partial_response, results

    def extract_keywords(self, question):
        zju_entities = [
            "求是书院", "国立浙江大学", "浙大西迁", "竺可桢", "林启", "蒋梦麟",
            "四校合并", "院系调整", "杭州大学", "浙江农业大学", "浙江医科大学",
            "东方剑桥", "文军长征", "遵义", "湄潭", "宜山", "建德"
        ]
        keywords = []
        for entity in zju_entities:
            if entity in question:
                keywords.append(entity)
        time_patterns = [r'\d{4}年', r'\d{4}-\d{4}']
        for pattern in time_patterns:
            matches = re.findall(pattern, question)
            keywords.extend(matches)
        chinese_words = re.findall(r'[\u4e00-\u9fa5]{2,}', question)
        keywords.extend([word for word in chinese_words if word not in keywords])
        return keywords

    def understand_intent(self, question):
        q = question.lower()
        if any(word in q for word in ['什么时候', '何时', '哪一年', '成立时间']):
            return "time"
        elif any(word in q for word in ['谁', '人物', '校长', '教授']):
            return "person"
        elif any(word in q for word in ['哪里', '地点', '地方', '迁往']):
            return "location"
        elif any(word in q for word in ['什么', '哪些', '介绍', '解释']):
            return "fact"
        elif any(word in q for word in ['为什么', '原因', '为何']):
            return "reason"
        else:
            return "general"

    def generate_no_results_response(self, question, keywords):
        response = "抱歉，我没有找到关于这个问题的确切信息。\n\n"
        if keywords:
            response += f"我注意到您可能对以下内容感兴趣：{', '.join(keywords)}\n\n"
        response += "您可以尝试：\n"
        response += "• 换一种问法，比如 '浙江大学的历史' 而不是 '浙大过往'\n"
        response += "• 询问更具体的问题，如 '竺可桢校长的贡献'\n"
        response += "• 使用关键词查询，如 '西迁'、'四校合并' 等\n\n"
        response += "目前系统包含以下主要内容：\n"
        response += "- 浙江大学从1897年求是书院创立至今的发展历史\n"
        response += "- 抗战时期的西迁历程（建德、吉安、宜山、遵义、湄潭）\n"
        response += "- 1952年院系调整和1998年四校合并\n"
        response += "- 历任校长和著名教授的事迹\n"
        response += "- 各时期的重要成就和特色\n"
        return response

    def generate_response(self, question, results, intent):
        if self.llm.client:
            print("[Info] Using LLM for generation...")
            context_chunks = [r['document'] for r in results]
            response_text = self.llm.generate_answer(question, context_chunks, stream=False)
            if not isinstance(response_text, str):
                response_text = str(response_text)
            citations = "\n\n" + "─" * 30 + "\n**参考来源：**\n"
            for i, result in enumerate(results):
                meta = result['document'].get('metadata', {})
                source = meta.get('section_title') or meta.get('source') or '未知章节'
                citations += f"[{i+1}] {source} (相关度: {result['similarity']:.2f})\n"
            yield response_text + citations
            return
        response = f"关于『{question}』，我找到了以下信息：\n\n"
        if intent == "time":
            response += "时间相关信息：\n\n"
        elif intent == "person":
            response += "人物相关信息：\n\n"
        elif intent == "location":
            response += "地点相关信息：\n\n"
        elif intent == "reason":
            response += "原因相关信息：\n\n"
        else:
            response += "相关信息：\n\n"
        for i, result in enumerate(results):
            response += f"【信息 {i+1}】\n"
            meta = result['document'].get('metadata', {})
            src = meta.get('section_title') or meta.get('source') or '未知章节'
            response += f"来源：{src}\n"
            response += f"相关度：{result['similarity']:.4f}\n"
            response += f"内容：{result['content']}\n"
            metadata = result['document'].get('metadata', {})
            if metadata.get('persons'):
                response += f"涉及人物：{', '.join(metadata['persons'])}\n"
            if metadata.get('time_periods'):
                response += f"时间信息：{', '.join(metadata['time_periods'][:3])}\n"
            if metadata.get('locations'):
                response += f"相关地点：{', '.join(metadata['locations'][:3])}\n"
            response += "\n" + "─" * 50 + "\n\n"
        if len(results) > 0:
            response += "提示：如果这不是您想要的信息，可以尝试更具体的问题描述。"
        yield response

    def get_system_stats(self):
        if hasattr(self.vector_db, 'documents'):
            total_chunks = len(self.vector_db.documents)
            total_chars = sum(len(doc['content']) for doc in self.vector_db.documents)
            time_periods = set()
            persons = set()
            locations = set()
            institutions = set()
            for doc in self.vector_db.documents:
                metadata = doc.get('metadata', {})
                time_periods.update(metadata.get('time_periods', []))
                persons.update(metadata.get('persons', []))
                locations.update(metadata.get('locations', []))
                institutions.update(metadata.get('institutions', []))
            stats = f"""
系统统计信息

数据规模：
• 文本块数量：{total_chunks} 个
• 总字符数：{total_chars} 字
• 平均块大小：{total_chars/total_chunks:.0f} 字

内容覆盖：
• 时间范围：{len(time_periods)} 个时间段
• 涉及人物：{len(persons)} 位
• 相关地点：{len(locations)} 处  
• 机构组织：{len(institutions)} 个
"""
            return stats
        return "无法获取统计信息"

    def get_suggested_questions(self):
        suggestions = [
            "浙江大学的前身是什么？什么时候成立的？",
            "竺可桢校长对浙江大学有哪些重要贡献？",
            "浙大西迁的具体路线是怎样的？经过了哪些地方？",
            "什么是四校合并？具体是哪四所学校？",
            "求是书院的第一任负责人是谁？",
            "浙大为什么被称为'东方剑桥'？",
            "1952年院系调整对浙江大学有什么影响？",
            "浙大在遵义湄潭办学期间有哪些重要成就？",
            "浙江大学的校训'求是创新'是怎么来的？",
            "浙大现在有哪些校区？它们的历史分别是怎样的？"
        ]
        return suggestions

def create_enhanced_web_interface():
    system = EnhancedZJUHistorySystem()
    def respond(question, chat_history):
        formatted_history = []
        formatted_history.append({"role": "user","content": question})
        formatted_history.append({"role": "assistant","content": "正在思考..."})
        yield formatted_history, ""
        for response, results in system.smart_query(question):
            formatted_history[-1]["content"] = response
            yield formatted_history, ""
    def show_stats():
        return system.get_system_stats()
    def get_suggestions():
        suggestions = system.get_suggested_questions()
        return "\n".join([f"• {q}" for q in suggestions])
    def clear_chat():
        return [], ""
    with gr.Blocks(title="浙江大学校史智能问答系统", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 浙江大学校史智能问答系统")
        with gr.Row():
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(label="校史问答对话", height=500, show_copy_button=True, type="messages")
                with gr.Row():
                    question = gr.Textbox(label="请输入您关于浙大历史的问题", placeholder="例如：浙江大学什么时候成立的？浙大西迁经历了哪些地方？", lines=2, max_lines=4)
                    submit_btn = gr.Button("发送", variant="primary")
                with gr.Row():
                    clear_btn = gr.Button("清空对话", variant="secondary")
                    suggest_btn = gr.Button("查看推荐问题", variant="secondary")
            with gr.Column(scale=1):
                gr.Markdown("### 系统信息")
                stats_btn = gr.Button("显示系统统计", variant="primary")
                stats_output = gr.Textbox(label="系统统计", lines=10, interactive=False)
                suggestions_output = gr.Textbox(label="推荐问题", lines=8, interactive=False, visible=False)
        gr.Markdown("### 试试这些问题")
        examples = gr.Examples(
            examples=[
                "浙江大学的前身是什么？",
                "竺可桢校长对浙大有什么贡献？", 
                "浙大西迁经过了哪些地方？",
                "四校合并是哪四所学校？",
                "求是书院是什么时候成立的？"
            ],
            inputs=question,
            label="点击示例问题快速提问"
        )
        question.submit(respond, [question, chatbot], [chatbot, question])
        submit_btn.click(respond, [question, chatbot], [chatbot, question])
        clear_btn.click(clear_chat, None, [chatbot, question])
        stats_btn.click(show_stats, None, stats_output)
        suggest_btn.click(get_suggestions, None, suggestions_output)
    return demo

if __name__ == "__main__":
    demo = create_enhanced_web_interface()
    print("[INFO] Starting Web UI...")
    port_env = os.environ.get("GRADIO_SERVER_PORT")
    port = int(port_env) if port_env and port_env.isdigit() else None
    try:
        demo.launch(server_name="127.0.0.1", server_port=port, share=False, inbrowser=False)
    except OSError:
        demo.launch(server_name="127.0.0.1", server_port=None, share=False, inbrowser=False)
    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
