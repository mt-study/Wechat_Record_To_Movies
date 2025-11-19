auto.waitFor();
const PC_IP = "192.168.0.193";
const DETECT_URL = `http://${PC_IP}:5000/detect_voice`;
let lastVoiceCount = 0; // 记录上一屏的语音数量，用于判断是否滑动到底

// 核心：上传截图并获取语音信息
function getVoiceInfo() {
    try {
        // 截图
        java.lang.System.gc(); // 提前回收内存
        sleep(500);       
        let screen = images.captureScreen();
        let screenBitmap = screen.getBitmap();
        images.recycle(screen);
        
        // 转Base64
        let baos = new java.io.ByteArrayOutputStream();
        screenBitmap.compress(android.graphics.Bitmap.CompressFormat.JPEG, 80, baos);
        let base64 = android.util.Base64.encodeToString(baos.toByteArray(), android.util.Base64.NO_WRAP);
        baos.close();
        screenBitmap.recycle();
        
        // 发送请求
        let jsonStr = '{"image_base64":"' + base64.replace(/["\\]/g, '\\$&') + '"}';
        let requestBody = new java.lang.String(jsonStr);
        
        let url = new java.net.URL(DETECT_URL);
        let conn = url.openConnection();
        conn.setRequestMethod("POST");
        conn.setDoOutput(true);
        conn.setRequestProperty("Content-Type", "application/json");
        conn.setConnectTimeout(15000);
        conn.setReadTimeout(15000);
        
        let out = conn.getOutputStream();
        out.write(requestBody.getBytes("UTF-8"));
        out.flush();
        out.close();
        
        // 解析响应
        if (conn.getResponseCode() === 200) {
            let reader = new java.io.BufferedReader(
                new java.io.InputStreamReader(conn.getInputStream(), "UTF-8")
            );
            let response = "";
            let line;
            while ((line = reader.readLine()) !== null) response += line;
            reader.close();
            return JSON.parse(response);
        }
        return { status: "fail", msg: "请求失败" };
    } catch (e) {
        console.log("获取语音信息错误：" + e);
        return { status: "fail", msg: e.message };
    }
}

// 播放当前屏幕的语音
function playCurrentScreenVoices() {
    let result = getVoiceInfo();
    if (result.status !== "success" || result.total === 0) {
        toast("当前屏幕无语音");
        return 0; // 无语音
    }
    
    // 从上到下播放
    let voices = result.voices.sort((a, b) => a.y - b.y);
    let total = result.total;
    toast(`当前屏幕有${total}条语音，开始播放...`);
    sleep(1000);
    
    for (let i = 0; i < total; i++) {
        let voice = voices[i];
        let current = i + 1;
        let duration = voice.duration * 1000;
        toast(`播放 ${current}/${total} (${voice.duration}s)`);
        
        click(voice.x, voice.y);
        sleep(duration + 500); // 按时长等待
    }
    return total; // 返回当前屏幕播放的数量
}

// 主逻辑：循环播放+滑动屏幕
try {
    toast("开始处理多屏语音...");
    let screenCount = 1; // 记录当前是第几屏
    
    while (true) {
        toast(`正在处理第${screenCount}屏...`);
        let currentVoiceCount = playCurrentScreenVoices();
        
        // 判断是否需要滑动：当前屏幕有语音，且数量和上一屏不同（避免重复滑动）
        // if (currentVoiceCount === 0 || currentVoiceCount === lastVoiceCount) {
        //     toast("已无新语音，结束处理");
        //     break;
        // }
        
        // 滑动屏幕（向上滑动，加载下一屏，可根据实际界面调整参数）
        toast("滑动到下一屏...");
        let startX = device.width / 2; // 屏幕中间X
        let startY = device.height * 0.9; // 屏幕下方70%处
        let endY = device.height * 0.39; // 屏幕上方30%处
        swipe(startX, startY, startX, endY, 800); // 滑动时长500ms
        sleep(5000); // 等待页面加载
        
        // 更新记录，准备处理下一屏
        lastVoiceCount = currentVoiceCount;
        screenCount++;
    }
    
    toast("所有屏幕语音处理完成！");
} catch (e) {
    toast("错误：" + e.message);
    console.log(e);
}

exit();