auto.waitFor();
const PC_IP = "192.168.0.193";
const DETECT_URL = `http://${PC_IP}:5000/detect_voice`;

try {
    // 1. 截图上传
    toast("截图中...");
    let screen = images.captureScreen();
    let screenBitmap = screen.getBitmap();
    images.recycle(screen);
    
    let baos = new java.io.ByteArrayOutputStream();
    screenBitmap.compress(android.graphics.Bitmap.CompressFormat.JPEG, 80, baos);
    let base64 = android.util.Base64.encodeToString(baos.toByteArray(), android.util.Base64.NO_WRAP);
    baos.close();
    screenBitmap.recycle();
    
    // 2. 发送请求
    toast("识别语音和时长...");
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
    
    // 3. 按OCR时长播放
    let responseCode = conn.getResponseCode();
    if (responseCode === 200) {
        let reader = new java.io.BufferedReader(
            new java.io.InputStreamReader(conn.getInputStream(), "UTF-8")
        );
        let response = "";
        let line;
        while ((line = reader.readLine()) !== null) {
            response += line;
        }
        reader.close();
        
        let result = JSON.parse(response);
        if (result.status === "success" && result.total > 0) {
            let voices = result.voices.sort((a, b) => a.y - b.y); // 从上到下
            let total = result.total;
            toast(`共${total}条语音，开始播放...`);
            sleep(1000);
            
            for (let i = 0; i < total; i++) {
                let voice = voices[i];
                let current = i + 1;
                let duration = voice.duration * 1000; // 转毫秒
                toast(`播放 ${current}/${total} (${voice.duration}s)`);
                
                click(voice.x, voice.y);
                sleep(duration + 500); // 加500ms缓冲
            }
            
            toast(`全部播放完成！共${total}条`);
        } else {
            toast("未识别到语音：" + (result.msg || ""));
        }
    } else {
        toast("请求失败：" + responseCode);
    }
} catch (e) {
    toast("错误：" + e.message);
    console.log(e);
}

exit();