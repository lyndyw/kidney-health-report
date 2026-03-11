#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
营养报告数据提取脚本

从 PDF 或图片格式的营养报告中提取营养数据，输出结构化 JSON 数据。
支持文字版 PDF（pdfplumber）和扫描版/图片（OCR）两种处理方式。

使用方法:
    python3 extract_nutrition_data.py --input report.pdf --output nutrition_data.json
"""

import argparse
import json
import os
import re
import sys
from typing import Dict, List, Optional, Any

# 营养数据关键词映射表
NUTRITION_KEYWORDS = {
    'energy': ['能量', '热量', 'Energy', 'energy', '热能', '总能量'],
    'protein': ['蛋白质', '蛋白', 'Protein', 'protein', '优质蛋白'],
    'carbohydrate': ['碳水化合物', '碳水', 'Carbohydrate', 'carbohydrate', '糖类'],
    'fat': ['脂肪', 'Fat', 'fat', '脂类', '总脂肪'],
    'sodium': ['钠', 'Na', 'Sodium', 'sodium', '钠盐'],
    'potassium': ['钾', 'K', 'Potassium', 'potassium'],
    'phosphorus': ['磷', 'P', 'Phosphorus', 'phosphorus'],
    'calcium': ['钙', 'Ca', 'Calcium', 'calcium'],
    'iron': ['铁', 'Fe', 'Iron', 'iron'],
    'water': ['水', '水分', 'Fluid', 'fluid', '饮水量', '摄入量'],
    'fiber': ['膳食纤维', '纤维', 'Fiber', 'fiber', '纤维素'],
    'cholesterol': ['胆固醇', 'Cholesterol', 'cholesterol'],
    'vitamin_a': ['维生素 A', 'VA', '视黄醇'],
    'vitamin_c': ['维生素 C', 'VC', '抗坏血酸'],
    'vitamin_d': ['维生素 D', 'VD'],
    'vitamin_e': ['维生素 E', 'VE'],
    'zinc': ['锌', 'Zn', 'Zinc'],
    'magnesium': ['镁', 'Mg', 'Magnesium'],
}

# 单位映射
UNIT_MAPPING = {
    'kcal': 'kcal',
    '千卡': 'kcal',
    '大卡': 'kcal',
    'kJ': 'kJ',
    '千焦': 'kJ',
    'g': 'g',
    '克': 'g',
    'mg': 'mg',
    '毫克': 'mg',
    'μg': 'μg',
    '微克': 'μg',
    'ml': 'ml',
    '毫升': 'ml',
    'L': 'L',
    '升': 'L',
}


def extract_text_from_pdf(pdf_path: str) -> str:
    """从 PDF 文件提取文本"""
    try:
        import pdfplumber
    except ImportError:
        print("错误：需要安装 pdfplumber，运行：pip install pdfplumber")
        sys.exit(1)

    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

                # 提取表格
                tables = page.extract_tables()
                for table in tables:
                    if table:
                        for row in table:
                            if row:
                                for cell in row:
                                    if cell:
                                        text += str(cell) + " "
                                text += "\n"
    except Exception as e:
        print(f"PDF 提取失败：{e}")
        return ""

    return text


def extract_text_from_image(image_path: str) -> str:
    """从图片提取文本（OCR）"""
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        print("错误：需要安装 pytesseract 和 Pillow")
        print("运行：pip install pytesseract Pillow")
        print("还需要安装 Tesseract OCR 引擎")
        sys.exit(1)

    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang='chi_sim+eng')
        return text
    except Exception as e:
        print(f"OCR 提取失败：{e}")
        return ""


def extract_text_from_pdf_as_images(pdf_path: str) -> str:
    """将 PDF 转为图片后进行 OCR（针对扫描版 PDF）"""
    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError:
        print("错误：需要安装 pdf2image 和 pytesseract")
        print("运行：pip install pdf2image pytesseract")
        print("还需要安装 poppler 和 Tesseract OCR")
        sys.exit(1)

    text = ""
    try:
        images = convert_from_path(pdf_path, dpi=300)
        for i, image in enumerate(images):
            page_text = pytesseract.image_to_string(image, lang='chi_sim+eng')
            text += page_text + "\n"
    except Exception as e:
        print(f"扫描版 PDF 提取失败：{e}")

    return text


def parse_number(value_str: str) -> Optional[float]:
    """从字符串中提取数值"""
    if not value_str:
        return None

    # 处理范围，如 "1500-1800"
    range_match = re.search(r'(\d+(?:\.\d+)?)\s*[-~～]\s*(\d+(?:\.\d+)?)', value_str)
    if range_match:
        low = float(range_match.group(1))
        high = float(range_match.group(2))
        return (low + high) / 2  # 返回平均值

    # 提取单个数值
    number_match = re.search(r'(\d+(?:\.\d+)?)', value_str)
    if number_match:
        return float(number_match.group(1))

    return None


def parse_unit(value_str: str) -> str:
    """从字符串中提取单位"""
    if not value_str:
        return ""

    for cn, en in UNIT_MAPPING.items():
        if cn in value_str:
            return en

    return ""


def find_nutrition_value(text: str, nutrient: str) -> Optional[Dict[str, Any]]:
    """在文本中查找特定营养素的值"""
    keywords = NUTRITION_KEYWORDS.get(nutrient, [])

    for keyword in keywords:
        # 模式 1: 关键词 + 数值 + 单位，如 "能量 1800kcal"
        pattern1 = rf'{keyword}[:：\s]*(\d+(?:\.\d+)?\s*(?:[-~～]\s*\d+(?:\.\d+)?)?\s*(?:kcal|千卡 | 大卡|kJ|千焦|g|克|mg|毫克|μg|微克|ml|毫升|L|升)?)'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            value_str = match.group(1)
            value = parse_number(value_str)
            unit = parse_unit(value_str)
            if value:
                return {'value': value, 'unit': unit, 'raw': value_str}

        # 模式 2: 表格形式，关键词在数值前面
        pattern2 = rf'{keyword}[:：\s]*(\d+(?:\.\d+)?)'
        match = re.search(pattern2, text, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            return {'value': value, 'unit': '', 'raw': match.group(1)}

    return None


def extract_nutrition_data(text: str) -> Dict[str, Any]:
    """从文本中提取所有营养数据"""
    data = {
        'energy': None,
        'protein': None,
        'carbohydrate': None,
        'fat': None,
        'sodium': None,
        'potassium': None,
        'phosphorus': None,
        'calcium': None,
        'iron': None,
        'water': None,
        'fiber': None,
        'meal_ratio': {'breakfast': 30, 'lunch': 40, 'dinner': 30},  # 默认餐次比
    }

    # 提取各项营养素
    nutrient_map = {
        'energy': '能量',
        'protein': '蛋白质',
        'carbohydrate': '碳水化合物',
        'fat': '脂肪',
        'sodium': '钠',
        'potassium': '钾',
        'phosphorus': '磷',
        'calcium': '钙',
        'iron': '铁',
        'water': '水',
        'fiber': '膳食纤维',
    }

    for key, name in nutrient_map.items():
        result = find_nutrition_value(text, key)
        if result:
            data[key] = result

    # 尝试提取餐次比
    meal_pattern = r'早餐[:：\s]*(\d+)%?[:：\s/]*午餐[:：\s]*(\d+)%?[:：\s/]*晚餐[:：\s]*(\d+)%?'
    match = re.search(meal_pattern, text)
    if match:
        data['meal_ratio'] = {
            'breakfast': int(match.group(1)),
            'lunch': int(match.group(2)),
            'dinner': int(match.group(3)),
        }

    return data


def process_file(input_path: str) -> Dict[str, Any]:
    """处理输入文件，提取营养数据"""
    if not os.path.exists(input_path):
        print(f"错误：文件不存在：{input_path}")
        sys.exit(1)

    file_ext = os.path.splitext(input_path)[1].lower()
    text = ""

    print(f"正在处理文件：{input_path}")

    if file_ext == '.pdf':
        # 先尝试文字版 PDF
        text = extract_text_from_pdf(input_path)
        if not text.strip():
            print("文字版 PDF 提取失败，尝试扫描版 OCR...")
            text = extract_text_from_pdf_as_images(input_path)
    elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
        text = extract_text_from_image(input_path)
    else:
        print(f"不支持的文件格式：{file_ext}")
        sys.exit(1)

    if not text.strip():
        print("警告：未能从文件中提取到文本内容")
        return {}

    # 提取营养数据
    data = extract_nutrition_data(text)
    data['source_file'] = input_path
    data['extracted_text_length'] = len(text)

    return data


def main():
    parser = argparse.ArgumentParser(description='从营养报告 PDF/图片中提取营养数据')
    parser.add_argument('--input', '-i', required=True, help='输入文件路径（PDF 或图片）')
    parser.add_argument('--output', '-o', help='输出 JSON 文件路径（可选）')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细信息')

    args = parser.parse_args()

    # 处理文件
    data = process_file(args.input)

    # 输出结果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"数据已保存到：{args.output}")
    else:
        print("\n=== 提取的营养数据 ===")
        print(json.dumps(data, ensure_ascii=False, indent=2))

    # 显示提取摘要
    print("\n=== 提取摘要 ===")
    for key, name in [
        ('energy', '能量'),
        ('protein', '蛋白质'),
        ('carbohydrate', '碳水化合物'),
        ('fat', '脂肪'),
        ('sodium', '钠'),
        ('potassium', '钾'),
        ('phosphorus', '磷'),
        ('calcium', '钙'),
        ('iron', '铁'),
    ]:
        value = data.get(key)
        if value and value.get('value'):
            print(f"{name}: {value['value']} {value.get('unit', '')}")
        else:
            print(f"{name}: 未提取到数据")


if __name__ == '__main__':
    main()
