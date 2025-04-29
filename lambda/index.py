# lambda/index.py
import json
import os
import re  # 正規表現モジュールをインポート
import requests # FastAPIへのHTTPリクエスト用


# モデル推論サーバーのURL
MODEL_URL = "https://cd61-34-143-183-144.ngrok-free.app" #day1_practice.ipynbのFastAPIを立ち上げ時の公開URL

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))
        
        # Cognitoで認証されたユーザー情報を取得
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")
        
        # リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])

        print("Processing message:", message)
        print("Using model:", MODEL_URL)
        
        # # 会話履歴を使用
        # messages = conversation_history.copy()
        
        # # ユーザーメッセージを追加
        # messages.append({
        #     "role": "user",
        #     "content": message
        # })
        
        # # Nova Liteモデル用のリクエストペイロードを構築
        # # 会話履歴を含める
        # bedrock_messages = []
        # for msg in messages:
        #     if msg["role"] == "user":
        #         bedrock_messages.append({
        #             "role": "user",
        #             "content": [{"text": msg["content"]}]
        #         })
        #     elif msg["role"] == "assistant":
        #         bedrock_messages.append({
        #             "role": "assistant", 
        #             "content": [{"text": msg["content"]}]
        #         })
        
        # invoke_model用のリクエストペイロード
        # 最新のユーザーメッセージのみ使用（履歴は使わない設計ならここだけでOK）
        request_payload = {
            "prompt": message,
            "max_new_tokens": 512,
            "do_sample": True,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        print("Sending request to FastAPI model server with payload:", json.dumps(request_payload))
        
         # FastAPIへPOSTリクエスト
        response = requests.post(MODEL_URL, json=request_payload)

        if response.status_code != 200:
            raise Exception(f"FastAPI server returned status {response.status_code}: {response.text}")
        
        response_data = response.json()
        
        # アシスタント(モデルから)の応答を取得
        assistant_response = response_data.get("generated_text", "")
        if not assistant_response:
            raise Exception("No generated_text found in the response")
        
        # アシスタントの応答を会話履歴に追加
        conversation_history.append({
            "role": "user",
            "content": message
        })
        conversation_history.append({
            "role": "assistant",
            "content": assistant_response
        })
        
        # 成功レスポンスの返却
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": conversation_history
            })
        }
        
    except Exception as error:
        print("Error:", str(error))
        
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }
