from ultralytics import YOLO
import base64
import pytesseract
from PIL import Image, ImageDraw, ImageEnhance
import io
import re
from flask import Flask, request, jsonify
# 替换为你的实际安装路径（注意双斜杠“\\”）
pytesseract.pytesseract.tesseract_cmd = r"H:\DeepLearn\Tesseract-OCR\tesseract.exe"


# 配置YOLO模型和Tesseract路径（替换为你的实际路径）
model = YOLO(r"Z:\py project\Wechat_Record_To_Movies\Yolo_Train\runs\voice_detect_final21\weights\best.pt")
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Windows示例路径
CLASS_NAMES=['me','other']
app = Flask(__name__)

def ocr_extract_duration(img_crop):
    pytesseract.pytesseract.tesseract_cmd = r"H:\DeepLearn\Tesseract-OCR\tesseract.exe"
    """优化后：增强文字清晰度，提高识别率"""
    try:
        # 1. 增强对比度（让文字更黑、背景更白）
        enhancer = ImageEnhance.Contrast(img_crop)
        img_crop = enhancer.enhance(3.0)  # 对比度从2.0提到3.0，可根据实际调整
        
        # 2. 转灰度图（减少颜色干扰）
        img_gray = img_crop.convert("L")
        
        # 3. 二值化（关键！突出文字，去除模糊）
        threshold = 150  # 阈值（可调整：120-180，数值越高文字越粗）
        img_binary = img_gray.point(lambda p: 255 if p > threshold else 0)  # 文字变白，背景变黑
        
        # 4. 轻微膨胀（让细文字变粗，避免OCR漏识别）
        from PIL import ImageFilter
        img_binary = img_binary.filter(ImageFilter.MaxFilter(1))
        
        # 5. OCR识别（优化配置）
        # lang="eng+chi_sim"：同时支持英文（s/″）和中文（秒）
        # 只保留数字和时间单位，减少干扰
        text = pytesseract.image_to_string(
            img_binary, 
            lang="eng+chi_sim", 
            config="--psm 7 -c tessedit_char_whitelist=0123456789s″秒"
        )
        
        # 提取数字（忽略单位）
        duration = re.search(r"\d+", text.strip())
        result = int(duration.group()) if duration else 3
        print(f"OCR识别：原始文字={text.strip()} → 提取时长={result}s")  # 打印中间结果
        return result
    except Exception as e:
        print(f"OCR识别失败：{e}")
        return 3

@app.route("/detect_voice", methods=["POST"])
def detect_voice():
    try:
        # 1. 接收手机图片
        data = request.get_json()
        img_base64 = data.get("image_base64")
        if not img_base64:
            return jsonify({"status": "fail", "msg": "未收到图片"})
        
        # 2. 解码图片
        img_base64 = img_base64.replace(" ", "").replace("\n", "")
        img_data = base64.b64decode(img_base64)
        img = Image.open(io.BytesIO(img_data)).convert("RGB")
        draw = ImageDraw.Draw(img)
        
        # 3. YOLO识别语音图标
        results = model(img, conf=0.2)
        voice_info = []  # 存储每个语音的坐标和时长
        
        for r in results:
            boxes = r.boxes.data.cpu().numpy()
            for box in boxes:
                x1, y1, x2, y2, conf, cls = box[:6]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                cls = int(cls)  # 类别索引（0、1、2...）
                class_name = CLASS_NAMES[cls]  # 获取类别名称（如"voice"）
                confidence = round(float(conf), 2)

                if class_name == "me":
                    # 4. 裁剪语音时长显示区域（根据实际界面调整，示例：语音框右侧200x50区域）
                    # （需要你根据手机截图中“时长”的位置微调，确保裁剪到正确区域）
                    duration_x1 = x1 -80  # 语音框右侧10px开始
                    duration_y1 = y1   # 语音框上方10px
                    duration_x2 = duration_x1 + 55  # 宽度100px
                    duration_y2 = y2   # 高度40px
                    # 确保裁剪区域在图片内
                    duration_x1 = max(0, duration_x1)
                    duration_y1 = max(0, duration_y1)
                    duration_x2 = min(img.width, duration_x2)
                    duration_y2 = min(img.height, duration_y2)
                    # 裁剪时长区域
                    duration_crop = img.crop((duration_x1, duration_y1, duration_x2, duration_y2))
                    # duration_crop.save(f"./OCR_cutpic/duration_crop_{len(voice_info)}.jpg")  # 保存为图片文件
                    
                    # 5. OCR识别时长
                elif class_name == "other":
                    # 4. 裁剪语音时长显示区域（根据实际界面调整，示例：语音框右侧200x50区域）
                    # （需要你根据手机截图中“时长”的位置微调，确保裁剪到正确区域）
                    duration_x1 = x2 + 20  # 语音框右侧10px开始
                    duration_y1 = y1   # 语音框上方10px
                    duration_x2 = duration_x1 + 55  # 宽度100px
                    duration_y2 = y2   # 高度40px
                    # 确保裁剪区域在图片内
                    duration_x1 = max(0, duration_x1)
                    duration_y1 = max(0, duration_y1)
                    duration_x2 = min(img.width, duration_x2)
                    duration_y2 = min(img.height, duration_y2)
                    # 裁剪时长区域
                    duration_crop = img.crop((duration_x1, duration_y1, duration_x2, duration_y2))
                    # duration_crop.save(f"./OCR_cutpic/duration_crop_{len(voice_info)}.jpg")  # 保存为图片文件
                    
                    # 5. OCR识别时长
                duration = ocr_extract_duration(duration_crop)
                
                # 6. 标注（语音框+时长）
                draw.rectangle([x1, y1, x2, y2], outline="red", width=3)  # 语音框
                draw.rectangle([duration_x1, duration_y1, duration_x2, duration_y2], outline="blue", width=2)  # 时长区域
                # draw.text((x1, y1-20), f"Voice {duration}s", fill="red")  # 显示识别的时长

                # 标注内容：类别名称 + 置信度 + 时长
                draw.text((x1, y1-20), f"{class_name} {confidence} → {duration}s", fill="red")
                
                # 7. 记录坐标和时长
                voice_info.append({
                    "x": int((x1 + x2)/2),  # 中心点X
                    "y": int((y1 + y2)/2),  # 中心点Y
                    "duration": duration  # 识别的秒数
                })
        
        # 显示标注后的图片（验证识别结果）
        img.show()
        print(f"识别到{len(voice_info)}条语音，时长分别为：{[v['duration'] for v in voice_info]}")
        
        # 8. 返回结果给手机
        return jsonify({
            "status": "success",
            "voices": voice_info,  # 包含x、y、duration
            "total": len(voice_info)
        })
    
    except Exception as e:
        print(f"错误：{str(e)}")
        return jsonify({"status": "fail", "msg": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)