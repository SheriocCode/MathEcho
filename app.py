# -*- coding: utf-8 -*-
from flask import Flask, Response, request
from http import HTTPStatus
from flask_cors import CORS
from openai import OpenAI
from dashscope import Application
import json
import requests
import uuid
from rich.console import Console
from concurrent.futures import ThreadPoolExecutor

from db import add_knowledge_search_result, create_apisession, get_apisession, init_db, create_session, add_question_to_session, add_question_answer, get_answer_by_question_id, add_question_summary, get_question_by_id, add_web_search_result, get_retrieve_data
from utils.result import success_response, error_response
from config import AppConfig, ApiKeyConfig, PromptConfig



app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=5)

CORS(app, resources=r'/*') 

app.config.from_object(AppConfig)

qwen_client = OpenAI(
    api_key=ApiKeyConfig.QWEN_API_KEY,
    base_url=ApiKeyConfig.QWEN_BASE_URL
)

zhipu_client = OpenAI(
    api_key=ApiKeyConfig.ZHIPU_API_KEY,
    base_url=ApiKeyConfig.ZHIPU_BASE_URL 
)

console = Console()

def extract_search_keywords(user_question):
    prompt = PromptConfig.KEYWORD_EXTRACTION_PROMPT + f'用户问题：{user_question}'

    response = qwen_client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    
    console.print(f"[yellow](func: extract_search_keywords)[yellow] [green]response:{response}[/green] ")

    try:
        result = json.loads(response.choices[0].message.content)
        if result["related"]:
            return result["keywords"]
        else:
            return []
    except Exception as e:
        console.print(f"[red]Error parsing response: {e}[/red]")
        return []

@app.route("/newchat", methods=["GET"])
def new_chat():
    session_id = uuid.uuid4().hex
    success, msg = create_session(session_id)
    if not success:
        return error_response(msg)
    return success_response({"session_id": msg})

@app.route("/new_question_id", methods=["POST"])
def new_question_id():
    session_id = request.cookies.get('session_id')
    if not session_id:
        return error_response("Session ID not found")

    data = request.json
    content = {
        "user_question": data.get("user_question"),
        "ocr_msg": data.get("ocr_msg")
    }

    success, msg = add_question_to_session(session_id, json.dumps(content))
    if not success:
        return error_response(msg)

    return success_response({"question_id": msg})

@app.route("/knowledge_search", methods=["POST"])
def knowledge_search():
    session_id = request.cookies.get('session_id')
    if not session_id:
        return error_response("Session ID not found")

    data = request.json
    question_id = data.get("question_id")
    success, msg = get_question_by_id(question_id)
    if not success:
        return error_response(msg)
    user_question = json.loads(msg.content)["user_question"]

    # 意图识别
    completion = qwen_client.chat.completions.create(
        model="qwen-plus", 
        messages=[
            {'role': 'system', 'content': '你需要对用户的问题进行分类，判断是否属于数学相关的问题，若是，则返回1，否则返回0'},
            {'role': 'user', 'content': user_question}
            ]
    )
    console.print(f"[yellow](func: knowledge_search)[yellow] [green]意图识别结果:{completion.choices[0].message.content}[/green] ")
    if completion.choices[0].message.content != '1':
        return error_response("No need to search")
    
    # 知识检索
    completion = qwen_client.chat.completions.create(
        model="qwen-plus", 
        messages=[
            {'role': 'system', 'content': '根据用户问题判断和下列哪种类别最相关，给出且仅给出一个类别id，例如：17。类别如下：' + str(knowledge_keywords)},
            {'role': 'user', 'content': user_question}
            ]
    )
    console.print(f"[yellow](func: knowledge_search)[yellow] [green]类别id:{completion.choices[0].message.content}[/green] ")
    category_id = completion.choices[0].message.content
    for item in knowledge_data:
        if str(item['id']) == str(category_id):
            res = []
            res.append({
                "title": item.get("title", ""),  # 如果没有找到 "title"，返回空字符串
                "content": {
                    "basic_concept": item.get("content", {}).get("basic_concept", ""),
                    "basic_operation": item.get("content", {}).get("basic_operation", ""),
                    "common_theorems": item.get("content", {}).get("common_theorems", ""),
                    "example_problems": item.get("content", {}).get("example_problems", ""),
                    "solving_tips": item.get("content", {}).get("solving_tips", "")
                }
            })

    # TODO: 数据入库
    add_knowledge_search_result(question_id, json.dumps(res))
    return success_response({"type": "knowledge_search_result", "knowledge_items": res})

@app.route("/web_search", methods=["POST"])
def web_search():
    session_id = request.cookies.get('session_id')
    if not session_id:
        return error_response("Session ID not found")
    
    data = request.json
    question_id = data.get("question_id")
    success, msg = get_question_by_id(question_id)

    if not success:
        return error_response(msg)
    
    user_question = json.loads(msg.content)["user_question"]

    # 用户问题关键词提取
    console.print(f'[blue]@web_search - extract keywords[/blue]')
    keywords = extract_search_keywords(user_question)
    if not keywords:
        return error_response("No need to search")
    

    # 调用zhipu API 进行搜索
    console.print(f'[blue]@web_search - start search[/blue]')
    resp = requests.post(
        ApiKeyConfig.ZHIPU_BASE_URL,
        json = {
            "request_id": str(uuid.uuid4()),
            "tool": "web-search-pro",
            "stream": False,
            "messages": [
                {
                    "role": "user",
                    "content": ' '.join(keywords)
                }
            ]
        },
        headers={'Authorization': ApiKeyConfig.ZHIPU_API_KEY},
        timeout=300
    )

    search_res = json.loads(resp.content.decode())["choices"][0]["message"]["tool_calls"][1]["search_result"]

    # 搜索结果入库
    console.print(f'[blue]@web_search - save to db [/blue]')
    # TODO: 整理搜索结果，保留关键信息
    add_web_search_result(question_id, json.dumps(search_res))

    return success_response({"type": "web_search_result", "web_search_items": search_res})


@app.route("/rag_search", methods=["POST"])
def rag_search():
    session_id = request.cookies.get('session_id')
    if not session_id:
        return error_response("Session ID not found")

    data = request.json
    question_id = data.get("question_id")
    success, msg = get_question_by_id(question_id)

    # rag 搜索
    # TODO: rag 搜索，基于rag-agent

    # TODO: 搜索结果入库
    pass


# 后台进程：对话总结
def background_summary(question_id, full_response):
    response = qwen_client.chat.completions.create(
        model="qwen-plus", 
        messages=[
            {'role': 'system', 'content': 'summarize the following text into a concise summary, without repeating the text'},
            {'role': 'user', 'content': full_response}],
    )
        
    summary = response.choices[0].message.content if response.choices else "No response"
    console.print(f'[purple](back func: background_summary)[/purple] [italic green]summary_result: {summary}[/italic green]')

    try:
        with app.app_context():
            add_question_summary(question_id, summary)
        console.print(f"[purple](back func: background_summary)Summary saved successfully[/purple]")
    except Exception as e:
        console.print(f"[red]Error submitting background task: {e}[/red]")


@app.route("/stream_chat", methods=["POST"])
def stream_chat():
    session_id = request.cookies.get('session_id')
    if not session_id:
        return error_response("Session ID not found")

    data = request.json
    question_id = data.get("question_id")
    success, msg = get_question_by_id(question_id)
    if not success:
        return error_response(msg)

    user_input = json.loads(msg.content)

    # 获取retrieve 数据
    console.print(f'[blue]@stream_chat - get retrieve data[/blue]')
    success, retrieve_data = get_retrieve_data(question_id)
    if success:
        console.print(f"[green]retrieve data:[/green]")
        console.print(f"[green]web_search_result: {retrieve_data['web_search_result'][:25]}...[/green]")
        console.print(f"[green]rag_result: {retrieve_data['rag_result'][:25]}...[/green]")
        console.print(f"[green]knowledge_search_result: {retrieve_data['knowledge_search_result'][:25]}...[/green]")
    else:
        console.print(f"[red]Failed to retrieve data for question_id: {question_id}[/red]")

    # 构建消息列表
    messages = []

    messages.append({
        "role": "system",
        "content": """
        你是一个智能助手，你需要参考引用内容首先进行引用内容的思考（需要给出参考的具体引用），然后对用户的问题进行回答。
        """
    })

    messages.append({
        "role": "user",
        "content": """
        引用内容：{json_retrieve_data}
        1. 问题：{user_question}
        2. 图片ocr 识别结果：{ocr_msg}
        """.format(user_question=user_input.get("user_question"), ocr_msg=user_input.get("ocr_msg"), json_retrieve_data=str(retrieve_data))
    })


    console.print(f'[blue]@stream_chat - start stream chat[/blue]')
    # response = qwen_client.chat.completions.create(
    #     model="qwen-plus",
    #     messages=messages,
    #     stream=True
    # )
    # def generate():
    #     full_response = ""
    #     for chunk in response:
    #         if chunk.choices:
    #             content = chunk.choices[0].delta.content
    #             full_response += content
    #             print(content, end='')
    #             yield content

    #     with app.app_context():
    #         # 回答入库
    #         console.print(f'\n[blue]@stream_chat - save to db(add_question_answer)[/blue]')
    #         add_question_answer(question_id, full_response)

    #         # 后台进程：对话总结
    #         console.print(f'\n[blue]@stream_chat - start background summary[/blue]')
    #         executor.submit(background_summary, question_id, full_response)

    # 获取api_session_id
    success, api_session_id = get_apisession(session_id)
    if not api_session_id:
        # 第一次对话
        responses = Application.call(
                api_key=ApiKeyConfig.DASHSCOPE_API_KEY, 
                app_id=ApiKeyConfig.LONG_SESSION_AGENT_ID,
                prompt='{user_question} {ocr_msg}'.format(user_question=user_input.get("user_question"), ocr_msg=user_input.get("ocr_msg")),
                stream=True,  # 流式输出
                incremental_output=True)  # 增量输出
    else:
        responses = Application.call(
                api_key=ApiKeyConfig.DASHSCOPE_API_KEY, 
                app_id=ApiKeyConfig.LONG_SESSION_AGENT_ID,
                prompt='{user_question} {ocr_msg}'.format(user_question=user_input.get("user_question"), ocr_msg=user_input.get("ocr_msg")),
                session_id = api_session_id,
                stream=True,  # 流式输出
                incremental_output=True)  # 增量输出

    def generate():
        full_response = ""
        for response in responses:
            if response.status_code != HTTPStatus.OK:
                break
            else:
                content = response.output.text
                full_response += content
                # print(content, end='')
                yield content

        with app.app_context():
            # TODO: 结果入库
            console.print(f'\n[blue]@stream_chat - save to db(add_question_answer)[/blue]')
            add_question_answer(question_id, full_response)
            api_session_id = response.output.session_id
            create_apisession(session_id, api_session_id)

    return Response(generate(), content_type="text/plain")

@app.route("/recommend", methods=["POST"])
def recommend():
    session_id = request.cookies.get('session_id')
    if not session_id:
        return error_response("Session ID not found")

    data = request.json
    question_id = data.get("question_id")
    success, msg = get_question_by_id(question_id)
    if not success:
        return error_response(msg)

    success, text = get_answer_by_question_id(question_id)


    console.print(f'[blue]@recommend - start recommend[/blue] base_text: {text[:20]}...')


    response = qwen_client.chat.completions.create(
        model="qwen-max",
        messages=[
            {
            "role": "system",
            "content": '根据文本推荐3个与中学数学相关的问题，每个问题不超过15个字，只返回JSON数组。示例：["如何解一元二次方程？","一元二次方程的判别式是什么？","如何求二次函数的顶点？"]'
            },
            {"role": "user", "content": f"text: {text}"}
        ],
    )
    # 提取响应内容
    content = response.choices[0].message.content if response.choices else "No response"
    
    console.print(f'[blue]@recommend - recommend result: [/blue]{json.loads(content)}')

    return success_response({"recommend_items": json.loads(content)})


def read_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)  # 加载 JSON 数据
    return data

if __name__ == "__main__":
    # 缓存加载关键词
    knowledge_data = read_json_file('E:\Desktop\LawAI\Demo\文本解析\knowledge.json')
    knowledge_keywords = []
    for item in knowledge_data:
        knowledge_keywords.append({
            'id': item['id'],
            'keyword': item['title']
        })

    init_db(app)
    app.run(debug=True)