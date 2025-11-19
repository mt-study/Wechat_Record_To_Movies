import os
import xml.etree.ElementTree as ET

# 配置（按data.yaml修改，关键适配两类标签）
XML_FOLDERS = ["labels/train", "labels/val"]  # XML存放的文件夹
TXT_FOLDERS = ["labels/train", "labels/val"]  # TXT保存的文件夹
# 标签映射：XML中的旧标签 → (YOLO标签ID, 新标签名)，与data.yaml完全对应
LABEL_MAPPING = {
    "me": (0, "me"),    # 对应data.yaml的第1类（ID 0）
    "other": (1, "other")  # 对应data.yaml的第2类（ID 1）
}

# 转换函数（支持两类标签同时转换）
def xml_to_yolo(xml_path, txt_path, img_width, img_height):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    with open(txt_path, "w") as f:
        for obj in root.findall("object"):
            label = obj.find("name").text
            # 只处理映射中存在的标签（忽略其他无效标签）
            if label not in LABEL_MAPPING:
                print(f"⚠️  忽略未知标签：{label}（文件：{xml_path}）")
                continue

            # 获取当前标签对应的YOLO ID
            label_id, new_label = LABEL_MAPPING[label]

            # 解析XML中的边界框坐标
            bndbox = obj.find("bndbox")
            xmin = float(bndbox.find("xmin").text)
            ymin = float(bndbox.find("ymin").text)
            xmax = float(bndbox.find("xmax").text)
            ymax = float(bndbox.find("ymax").text)

            # 转换为YOLO格式（归一化坐标）
            x_center = (xmin + xmax) / (2 * img_width)
            y_center = (ymin + ymax) / (2 * img_height)
            width = (xmax - xmin) / img_width
            height = (ymax - ymin) / img_height

            # 写入TXT（格式：标签ID x_center y_center width height）
            f.write(f"{label_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")

# 批量转换所有XML文件
for xml_folder, txt_folder in zip(XML_FOLDERS, TXT_FOLDERS):
    if not os.path.exists(txt_folder):
        os.makedirs(txt_folder)  # 不存在则创建文件夹
    # 遍历文件夹下所有XML文件
    for xml_filename in os.listdir(xml_folder):
        if not xml_filename.endswith(".xml"):
            continue  # 跳过非XML文件
        # 构造文件路径
        xml_path = os.path.join(xml_folder, xml_filename)
        txt_filename = xml_filename.replace(".xml", ".txt")
        txt_path = os.path.join(txt_folder, txt_filename)
        # 解析XML获取图片宽高
        tree = ET.parse(xml_path)
        root = tree.getroot()
        img_width = int(root.find("size/width").text)
        img_height = int(root.find("size/height").text)
        # 执行转换
        xml_to_yolo(xml_path, txt_path, img_width, img_height)
        print(f"✅ 转换完成：{xml_filename} → {txt_filename}")

print("\n🎉 所有XML已转为YOLO格式TXT！（支持me/other两类标签）")