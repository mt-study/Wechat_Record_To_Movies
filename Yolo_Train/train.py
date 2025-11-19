from ultralytics import YOLO

if __name__ == '__main__':
    model = YOLO('yolov8n.pt')

    results = model.train(
        data='data.yaml',  # 已改为names: ['me']，无需修改
        epochs=50,         # 足够训练轮数，确保模型学到
        batch=4,           # CPU保持小批次，避免内存不足
        imgsz=640,         # 兼顾速度和准确率
        device='0',      # 无GPU保持cpu，有GPU改'0'
        patience=20,       # 20轮没提升再停止，避免提前终止
        save=True,
        project='runs',
        workers=0,  # 禁用多进程（Windows必设，否则报错）
        name='voice_detect_final',  # 新结果文件夹
        pretrained=True,
        augment=True,      # 数据增强（翻转、缩放），提升泛化能力
        mixup=0.2,         # 混合样本，减少过拟合
        lr0=0.001          # 降低学习率，让模型慢慢学透
    )