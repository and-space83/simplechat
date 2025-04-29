# lambda/index.py
import json
import os
import re  # 正規表現モジュールをインポート
import urllib.request # requestsの代わりに追加

# Lambda コンテキストからリージョンを抽出する関数（今は未使用）
def extract_region_from_arn(arn):
    match = re.search('arn:aws:lambda:([^:]+):', arn)
    if match:
        return match.group(1)
    return "us-east-1"  # デフォルト値

# FastAPIのエンドポイントURL
MODEL_URL = "https://00f5-35-198-247-4.ngrok-free.app/generate" # day1_practice.ipynbのFastAPIを立ち上げ時の公開URL

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
        
        # promptがなければmessageを代用
        prompt = body.get('prompt') or body.get('message')
        if not prompt:
            raise Exception("リクエストに 'prompt' または 'message' フィールドが含まれていません。")
        
        # FastAPIに送信するペイロード
        request_payload = json.dumps({
            "prompt": prompt,
            "max_new_tokens": 512,
            "do_sample": True,
            "temperature": 0.7,
            "top_p": 0.9
        }).encode("utf-8")
        
        # POSTリクエスト送信（method='POST'を明示）
        req = urllib.request.Request(
            MODEL_URL,
            data=request_payload,
            headers={"Content-Type": "application/json"},
            method="POST" # 明示的にPOST
        )
        
        with urllib.request.urlopen(req) as res:
            response_body = json.loads(res.read().decode("utf-8"))

        print("FastAPI server response:", json.dumps(response_body, ensure_ascii=False))

        assistant_response = response_body.get("generated_text", "")
        if not assistant_response:
            raise Exception("FastAPIサーバーから 'generated_text' を取得できませんでした。")
        response_time = response_body.get("response_time", 0)

        
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
                "response_time": response_time
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
