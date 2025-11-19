from ultralytics import YOLO
import cv2
import os

# --------------------
# 配置参数（按需修改）
# --------------------
MODEL_PATH = r"Z:\py project\Wechat_Record_To_Movies\Yolo_Train\runs\voice_detect_final21\weights\best.pt"  # 训练好的模型路径（默认不用改）
TEST_IMG_PATH = r"Z:\py project\Wechat_Record_To_Movies\Yolo_Train\bee7f29785866face4307a50475f5568.jpg"  # 单张测试图路径（可替换为你的测试图）
BATCH_TEST_FOLDER = "images/val"  # 批量测试文件夹（用验证集图片）
CONF_THRESHOLD = 0.3  # 置信度阈值（低于0.3的识别结果过滤掉）
DEVICE = "cpu"  # 测试设备（有GPU改"0"，CPU保持"cpu"）

# --------------------
# 加载模型
# --------------------
try:
    model = YOLO(MODEL_PATH)
    print(f"✅ 成功加载模型：{MODEL_PATH}")
except Exception as e:
    print(f"❌ 模型加载失败：{e}")
    exit()

# --------------------
# 功能1：单张图片测试（显示识别结果）
# --------------------
def test_single_image(img_path):
    if not os.path.exists(img_path):
        print(f"❌ 测试图不存在：{img_path}")
        return

    # 运行识别
    results = model(img_path, conf=CONF_THRESHOLD, device=DEVICE)

    # 处理识别结果
    for r in results:
        # 生成带标注框的图片（红色框标注语音图标，显示标签和置信度）
        annotated_img = r.plot(
            conf=True,  # 显示置信度
            labels=True,  # 显示标签（voice）
            line_width=2,  # 框线宽度
            font_size=1.0  # 字体大小
        )

        # 显示图片（窗口名+图片）
        cv2.imshow(f"单图测试结果 - {os.path.basename(img_path)}", annotated_img)
        print(f"✅ 单图测试完成，共识别到 {len(r.boxes)} 个语音图标")

    # 按任意键关闭窗口
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # 可选：保存测试结果图片
    save_path = "single_test_result.jpg"
    cv2.imwrite(save_path, annotated_img)
    print(f"✅ 测试结果已保存到：{save_path}")

# --------------------
# 功能2：批量测试（统计准确率、召回率）
# --------------------
def test_batch_images(folder_path):
    if not os.path.exists(folder_path):
        print(f"❌ 批量测试文件夹不存在：{folder_path}")
        return

    # 运行批量识别（save=True：保存带标注的结果图）
    results = model(folder_path, conf=CONF_THRESHOLD, device=DEVICE, save=True)

    # 统计整体性能（准确率、召回率、mAP50）
    metrics = model.val(data="data.yaml", device=DEVICE)  # 基于验证集计算指标
    print("\n📊 批量测试性能指标：")
    print(f"准确率（Precision）：{metrics.box.precision:.3f}")  # 识别对的比例
    print(f"召回率（Recall）：{metrics.box.recall:.3f}")      # 漏识别的比例（越低越好）
    print(f"mAP50：{metrics.box.map50:.3f}")                # 综合性能（越高越好，≥0.8合格）

    # 统计每张图的识别数量
    print("\n📋 单图识别统计：")
    for i, r in enumerate(results):
        img_name = os.path.basename(r.path)
        voice_count = len(r.boxes)
        print(f" - {img_name}：识别到 {voice_count} 个语音图标")

    # 批量结果保存路径（默认在 runs/voice_detect/predict ）
    print(f"\n✅ 批量测试结果已保存到：{results[0].save_dir}")

# --------------------
# 执行测试（二选一，注释掉不需要的）
# --------------------
# 1. 执行单张图片测试
test_single_image(TEST_IMG_PATH)

# 2. 执行批量测试（注释上面，打开下面）
# test_batch_images(BATCH_TEST_FOLDER)