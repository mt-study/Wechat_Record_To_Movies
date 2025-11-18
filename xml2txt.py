import os
import xml.etree.ElementTree as ET

# 配置（不用改）
XML_FOLDERS = ["labels/train", "labels/val"]  # XML存放的文件夹
TXT_FOLDERS = ["labels/train", "labels/val"]  # TXT保存的文件夹
OLD_LABEL = "me"  # 你的标注标签名
NEW_LABEL = "me"  # 和data.yaml保持一致（不用改）
LABEL_ID = 0  # 固定为0（只有1类）

# 转换函数
def xml_to_yolo(xml_path, txt_path, img_width, img_height):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    with open(txt_path, "w") as f:
        for obj in root.findall("object"):
            label = obj.find("name").text
            if label != OLD_LABEL:
                continue

            bndbox = obj.find("bndbox")
            xmin = float(bndbox.find("xmin").text)
            ymin = float(bndbox.find("ymin").text)
            xmax = float(bndbox.find("xmax").text)
            ymax = float(bndbox.find("ymax").text)

            x_center = (xmin + xmax) / (2 * img_width)
            y_center = (ymin + ymax) / (2 * img_height)
            width = (xmax - xmin) / img_width
            height = (ymax - ymin) / img_height

            f.write(f"{LABEL_ID} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")

# 批量转换
for xml_folder, txt_folder in zip(XML_FOLDERS, TXT_FOLDERS):
    if not os.path.exists(txt_folder):
        os.makedirs(txt_folder)
    for xml_filename in os.listdir(xml_folder):
        if not xml_filename.endswith(".xml"):
            continue
        xml_path = os.path.join(xml_folder, xml_filename)
        txt_filename = xml_filename.replace(".xml", ".txt")
        txt_path = os.path.join(txt_folder, txt_filename)
        tree = ET.parse(xml_path)
        root = tree.getroot()
        img_width = int(root.find("size/width").text)
        img_height = int(root.find("size/height").text)
        xml_to_yolo(xml_path, txt_path, img_width, img_height)
        print(f"✅ 转换完成：{xml_filename} → {txt_filename}")

print("\n🎉 所有XML已转为TXT！")