import os
from pyexpat.errors import messages
from random import choices

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()
app=Flask(__name__)

allowed=os.getenv("ALLOWED_ORIGINS","*").split(",")
CORS(app, resources={r"/api/*":{"origins":allowed}})

from openai import OpenAI
openai_client=OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

import google.generativeai as genai
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

deepseek_client=OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://openrouter.ai/api/v1")

def ask_openai(history,model="gpt-4o-mini"):
    messages=[]
    for h in history:
        if h["type"]=="user":
            role="user"
        else:
            role="assistant"
        messages.append({"role":role,"content":h["text"]})
    resp=openai_client.chat.completions.create(model=model,messages=messages)
    return resp.choices[0].message.content


def ask_gemini(history,model="gemini-2.5-flash"):
    parts=[]
    for h in history:
        if h["type"]=="user":
            role="user"
        else:
            role="assistant"
            parts.append({"role":role,"content":h["text"]})
    gen_model=genai.GenerativeModel(model)
    chat=gen_model.start_chat(history=parts)
    resp=chat.send_message(history[-1]["text"])
    return resp.text


def ask_deepseek(history,model="deepseek/deepseek-r1:free"):
    messages = []
    for h in history:
        if h["type"] == "user":
            role = "user"
        else:
            role = "assistant"
        messages.append({"role": role, "content": h["text"]})
    resp=deepseek_client.chat.completions.create(model=model,messages=messages)
    return resp.choices[0].message.content



@app.route("/api/respond", methods=["POST"])
def respond():
    data=request.get_json(force=True)
    history=data.get("history",[])
    provider=(data.get("model") or "").lower()
    prompt=data.get("prompt","").strip()
    if not history and prompt:
        history=[{"type":"user","text":prompt}]

    if not history:
        return jsonify({"error":"prompt required"}), 400

    try:
        if provider=="chatgpt":
            answer=ask_openai(history)
            return jsonify({
                "provider":"openai",
                "model":"gpt-4o-mini",
                "answer":answer
            })
        elif provider=="gemini":
            answer=ask_gemini(history)
            return jsonify({
                "provider":"gemini",
                "model":"gemini-2.5-flash",
                "answer":answer
            })
        elif provider=="deepseek":
            answer=ask_deepseek(history)
            return jsonify({
                "provider":"deepseek",
                "model":"deepseek-r1:free",
                "answer":answer
            })
        else:
            gpt_response=ask_openai(history)
            gemini_response=ask_gemini(history)
            deepseek_response=ask_deepseek(history)
            return jsonify({
                "provider":"all",
                "answers":{
                    "openai":gpt_response,
                    "gemini":gemini_response,
                    "deepseek":deepseek_response
                }
            })
    except Exception as e:
        return jsonify({"error":"failed","detail":str(e)}),500


@app.route("/api/hello",methods=["GET"])
def hello():
    return jsonify({"status":"ok","message":"Backend is running"})
if __name__=="__main__":
    app.run(host="127.0.0.1",port=5000,debug=True)