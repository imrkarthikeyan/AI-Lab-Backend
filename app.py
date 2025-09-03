import os
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

def ask_openai(prompt:str,model="gpt-4o-mini"):
    resp=openai_client.responses.create(model=model,input=prompt)
    return resp.output_text

def ask_gemini(prompt:str,model="gemini-2.5-flash"):
    resp=genai.GenerativeModel(model).generate_content(prompt)
    return resp.text

def ask_deepseek(prompt:str,model="deepseek/deepseek-r1:free"):
    resp=deepseek_client.chat.completions.create(model=model,messages=[{"role":"user","content":prompt}])
    return resp.choices[0].message.content



@app.route("/api/respond", methods=["POST"])
def respond():
    data=request.get_json(force=True)
    prompt=(data.get("prompt") or "").strip()
    provider=(data.get("model") or "").lower()
    if not prompt:
        return jsonify({"error":"prompt required"}),400
    if provider not in {"chatgpt","gemini","deepseek","all"}:
        return jsonify({"error":"invalid model"}),400
    try:
        if provider=="chatgpt":
            answer=ask_openai(prompt)
            return jsonify({
                "provider":"openai",
                "model":"gpt-4o-mini",
                "answer":answer
            })
        elif provider=="gemini":
            answer=ask_gemini(prompt)
            return jsonify({
                "provider":"gemini",
                "model":"gemini-2.5-flash",
                "answer":answer
            })
        elif provider=="deepseek":
            answer=ask_deepseek(prompt)
            return jsonify({
                "provider":"deepseek",
                "model":"deepseek-r1:free",
                "answer":answer
            })
        else:
            gpt_response=ask_openai(prompt)
            gemini_response=ask_gemini(prompt)
            deepseek_response=ask_deepseek(prompt)
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