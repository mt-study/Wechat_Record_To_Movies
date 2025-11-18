from ultralytics import YOLO
import base64
from PIL import Image
import io
from flask import Flask, request, jsonify
import json

# 加载模型（路径不变）
model = YOLO(r"Z:\py project\Wechat_Record_To_Movies\runs\voice_detect_final11\weights\best.pt")

app = Flask(__name__)

@app.route("/detect", methods=["POST"])
def detect_voice():
    try:
        # 优化：处理长Base64数据，关闭请求大小限制
        request.max_content_length = 10 * 1024 * 1024  # 允许10MB数据（足够截图）
        
        # 接收数据（兼容表单或JSON格式）
        if request.is_json:
            data = request.get_json()
            img_base64 = data.get("image_base64")
        else:
            img_base64 = request.form.get("image_base64")
        
        if not img_base64:
            return jsonify({"status": "fail", "msg": "未收到图片数据"})
        
        # 解码Base64（处理可能的空格/换行问题）
        img_base64 = img_base64.replace(" ", "").replace("\n", "").replace("\r", "")
        img_data = base64.b64decode(img_base64)
        img = Image.open(io.BytesIO(img_data))
        
        # YOLO识别
        results = model(img, conf=0.2)  # 降低置信度，提高识别率
        
        # 提取坐标
        voice_points = []
        for r in results:
            boxes = r.boxes.data.cpu().numpy()
            for box in boxes:
                x1, y1, x2, y2 = box[:4]
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                voice_points.append({"x": int(center_x), "y": int(center_y)})
        
        return jsonify({"status": "success", "points": voice_points})
    except Exception as e:
        print(f"识别错误：{str(e)}")
        return jsonify({"status": "fail", "msg": str(e)})

if __name__ == "__main__":
    # 启动服务，增加超时时间
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)