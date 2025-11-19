auto.waitFor();
const PC_IP = "192.168.0.193";
const DETECT_URL = `http://${PC_IP}:5000/detect_voice`;
 // 记录上一屏的语音数量，用于判断是否滑动到底

let lastImagePhash = "ffffffffffffffff"; // 上一屏图片的pHash值
const MAX_HAMMING_DISTANCE = 5; // 差异≤5判定为重复

// 核心1：前端计算图片pHash（纯JS，无需后端）
function calculatePhash(screen) {
    try {
        // 1. 先将截图转为Bitmap（确保是ARGB_8888格式，避免像素异常）
        let bitmap = screen.getBitmap();
        let argbBitmap = bitmap.copy(android.graphics.Bitmap.Config.ARGB_8888, false);
        // bitmap.recycle(); // 释放原Bitmap
        
        // 2. 缩小到8x8（用默认缩放模式，更稳定）
        let scaledBitmap = android.graphics.Bitmap.createScaledBitmap(argbBitmap, 8, 8, false);
        argbBitmap.recycle();
        
        // 3. 逐像素计算灰度（直接用getPixel，避免数组越界）
        let width = 8, height = 8;
        let grayValues = [];
        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                let pixel = scaledBitmap.getPixel(x, y);
                // 简化灰度计算（避免浮点数误差）
                let r = (pixel >> 16) & 0xff;
                let g = (pixel >> 8) & 0xff;
                let b = pixel & 0xff;
                let gray = Math.round((r + g + b) / 3); // 简化平均法，更稳定
                grayValues.push(gray);
            }
        }
        scaledBitmap.recycle();
        
        // 4. 计算平均灰度（过滤异常值）
        let validGrays = grayValues.filter(g => g >= 0 && g <= 255);
        if (validGrays.length === 0) return "0000000000000000";
        let avgGray = validGrays.reduce((sum, val) => sum + val, 0) / validGrays.length;
        
        // 5. 生成哈希（确保64位）
        let hashBits = "";
        for (let g of validGrays) {
            hashBits += g >= avgGray ? "1" : "0";
        }
        // 补全64位（防止像素数不足）
        hashBits = hashBits.padEnd(64, "0").slice(0, 64);
        
        // 6. 转为16位十六进制
        let phash = parseInt(hashBits, 2).toString(16).padStart(16, "0");
        console.log("计算出pHash：" + phash);
        return phash;
    } catch (e) {
        console.log("pHash计算失败：" + e);
        return "0000000000000000";
    }
}
// 核心2：计算汉明距离（对比哈希差异）
function calculateHammingDistance(hash1, hash2) {
    if (!hash1 || !hash2) return 100; // 任一为空，判定为不同
    // 转为64位二进制
    let bin1 = parseInt(hash1, 16).toString(2).padStart(64, "0");
    let bin2 = parseInt(hash2, 16).toString(2).padStart(64, "0");
    // 统计差异位数
    let distance = 0;
    for (let i = 0; i < 64; i++) {
        if (bin1[i] !== bin2[i]) distance++;
    }
    return distance;
}
// 核心：上传截图并获取语音信息
function getVoiceInfo() {
    try {
        // 截图
        java.lang.System.gc(); // 提前回收内存
        sleep(500);       
        let screen = images.captureScreen();
        let screenBitmap = screen.getBitmap();
        
        
        let currentPhash = calculatePhash(screen)
        
        log("当前屏pHash:", currentPhash, "上一屏pHash:", lastImagePhash);
        let distance = calculateHammingDistance(currentPhash, lastImagePhash);
        log("汉明距离:", distance);
        if (distance <= MAX_HAMMING_DISTANCE) {
            images.recycle(screen);
            return { status: "end", msg: "已滑动到底部" }; // 判定为重复，结束
        }
        else
        {
            lastImagePhash = currentPhash; // 更新上一屏pHash
        }
        
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

    if (result.status === "end") {
        toast("已滑动到底部，结束播放");
        exit();
    }

    if (result.status !== "success" || result.total === 0) {
        toast("当前屏幕无语音");
        return 0; // 无语音
    }
    log("检测到语音：", result.voices);
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
        

        
        // 滑动屏幕（向上滑动，加载下一屏，可根据实际界面调整参数）
        toast("滑动到下一屏...");
        let startX = device.width / 2; // 屏幕中间X
        let startY = device.height * 0.9; // 屏幕下方70%处
        let endY = device.height * 0.39; // 屏幕上方30%处
        swipe(startX, startY, startX, endY, 800); // 滑动时长500ms
        sleep(5000); // 等待页面加载
        

        screenCount++;
    }
    
    toast("所有屏幕语音处理完成！");
} catch (e) {
    toast("错误：" + e.message);
    console.log(e);
}

exit();