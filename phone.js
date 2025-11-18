auto.waitFor(); // 等待无障碍权限

// 配置区
const PC_IP = "192.168.0.193";
const PC_PORT = 5000;
const DETECT_URL = `http://${PC_IP}:${PC_PORT}/detect`;
let singleVoicePlayTime = 3000;
let totalVoices = 0;

// 步骤1：等待录屏
toast("3秒内启动录屏...");
sleep(3000);

// 兼容旧版AutoJS的图片压缩方法（不用images.scale）
function compressImage(img, targetWidth) {
    let width = img.getWidth();
    let height = img.getHeight();
    // 按宽度等比例计算新高度
    let targetHeight = Math.round((height * targetWidth) / width);
    // 用createScaledBitmap方法（所有版本都支持）
    return android.graphics.Bitmap.createScaledBitmap(img.getBitmap(), targetWidth, targetHeight, true);
}

// 核心：表单提交+兼容压缩
function getVoicePoints() {
    try {
        // 1. 截图→压缩→转Base64
        let screen = images.captureScreen();
        // 压缩到640px宽度（兼容旧版API）
        let compressedBitmap = compressImage(screen, 640);
        let compressedImg = images.fromBitmap(compressedBitmap);
        // 转Base64（质量50%）
        let imgBase64 = images.toBase64(compressedImg, "jpg", 50);
        
        // 回收资源
        images.recycle(screen);
        images.recycle(compressedImg);
        compressedBitmap.recycle();
        
        // 2. 表单提交Base64
        let formData = new FormData();
        formData.append("image_base64", imgBase64);
        
        let request = new http.Request();
        request.url = DETECT_URL;
        request.method = "POST";
        request.body = formData;
        
        let response = request.send();
        if (response.isSuccessful()) {
            let result = JSON.parse(response.body.string());
            if (result.status === "success") {
                return result.points;
            } else {
                toast("识别失败：" + result.msg);
                return [];
            }
        } else {
            toast("请求失败：" + response.statusCode);
            return [];
        }
    } catch (e) {
        toast("连接失败（查IP/WiFi）");
        console.log("错误：" + e);
        return [];
    }
}

// 只识别当前屏
let voicePoints = getVoicePoints();
if (voicePoints.length > 0) {
    voicePoints.sort((a, b) => a.y - b.y);
    for (let point of voicePoints) {
        totalVoices++;
        click(point.x, point.y);
        toast(`播放第${totalVoices}条语音`);
        sleep(singleVoicePlayTime);
    }
    toast(`当前屏播放完成！共${totalVoices}条`);
} else {
    toast("当前屏未识别到语音");
}

exit();