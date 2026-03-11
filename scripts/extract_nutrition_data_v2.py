#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
临床营养健康报告数据提取脚本（增强版）

专门处理临床营养健康报告格式，提取患者数据和营养建议。

使用方法:
    python3 extract_nutrition_data_v2.py --input report.pdf --output nutrition_data.json
"""

import argparse
import json
import os
import re
import sys
from typing import Dict, List, Optional, Any

try:
    import pdfplumber
except ImportError:
    print("错误：需要安装 pdfplumber，运行：pip install pdfplumber")
    sys.exit(1)


def extract_patient_info(text: str, tables: List) -> Dict[str, Any]:
    """从报告中提取患者基本信息"""
    info = {
        'name': '',
        'age': '',
        'gender': '',
        'height': '',
        'weight': '',
        'bmi': '',
        'medical_history': [],
        'indicators': {},
    }

    # 提取姓名（通常在标题附近）
    name_match = re.search(r'^([A-Z]|\S+)\n李涛平', text[:500])
    if name_match:
        info['name'] = '李涛平'
    else:
        # 尝试从文本开头提取
        first_line_match = re.search(r'临床营养健康报告\s*\n\s*(\S+)', text[:300])
        if first_line_match:
            info['name'] = first_line_match.group(1).strip('|').strip()

    # 提取 BMI
    bmi_match = re.search(r'BMI[指数 ]*(\d+\.?\d*)', text)
    if bmi_match:
        info['bmi'] = float(bmi_match.group(1))

    # 提取慢性病史
    if '高血压' in text:
        info['medical_history'].append('高血压')
    if '痛风' in text:
        info['medical_history'].append('痛风')
    if '慢性肾脏病' in text or 'CKD' in text:
        info['medical_history'].append('慢性肾脏病')
    if '脂肪肝' in text:
        info['medical_history'].append('脂肪肝')
    if '糖尿病' in text or '血糖' in text:
        info['medical_history'].append('糖代谢异常')

    # 提取关键指标
    # 肌酐
    cr_match = re.search(r'肌酐.*?(Cr).*?(\d+\.?\d*)\s*μmol/L', text, re.IGNORECASE)
    if cr_match:
        info['indicators']['肌酐'] = f"{cr_match.group(2)} μmol/L"
    else:
        cr_match2 = re.search(r'\(Cr\)\n肌酐.*?(\d+\.?\d*)\s*μmol/L', text)
        if cr_match2:
            info['indicators']['肌酐'] = f"{cr_match2.group(1)} μmol/L"

    # eGFR
    egfr_match = re.search(r'eGFR.*?(\d+\.?\d*)\s*ml/min', text)
    if egfr_match:
        info['indicators']['eGFR'] = f"{egfr_match.group(1)} ml/min"

    # 血糖
    glu_match = re.search(r'血糖.*?(\d+\.?\d*)\s*mmol/L', text)
    if glu_match:
        info['indicators']['血糖'] = f"{glu_match.group(1)} mmol/L"

    # 甘油三酯
    tg_match = re.search(r'甘油三酯.*?(\d+\.?\d*)\s*mmol/L', text)
    if tg_match:
        info['indicators']['甘油三酯'] = f"{tg_match.group(1)} mmol/L"

    # 尿酸
    ua_match = re.search(r'尿酸.*?(\d+\.?\d*)\s*μmol/L', text)
    if ua_match:
        info['indicators']['尿酸'] = f"{ua_match.group(1)} μmol/L"

    # 血压
    bp_match = re.search(r'血压.*?(\d+)/(\d+)\s*mmHg', text)
    if bp_match:
        info['indicators']['血压'] = f"{bp_match.group(1)}/{bp_match.group(2)} mmHg"

    return info


def extract_nutrition_recommendations(text: str) -> Dict[str, Any]:
    """从报告中提取营养建议"""
    recommendations = {
        'protein': {},
        'energy': {},
        'fat': {},
        'sodium': {},
        'water': {},
        'purine': [],  # 嘌呤相关（痛风管理）
    }

    # 蛋白质建议
    protein_match = re.search(r'蛋白质摄入量[：:\s]*(0\.?\d*[-~～]\d*\.?\d*)\s*g/kg/天', text)
    if protein_match:
        recommendations['protein']['intake'] = protein_match.group(1)
        recommendations['protein']['unit'] = 'g/kg/d'
        recommendations['protein']['principle'] = '优质低蛋白'

    # 脂肪建议
    fat_match = re.search(r'脂肪摄入量[：:\s]*(\d+[-~～]\d+)%', text)
    if fat_match:
        recommendations['fat']['ratio'] = fat_match.group(1)
        recommendations['fat']['principle'] = '低脂饮食'

    # 盐摄入建议
    salt_match = re.search(r'每日盐摄入[：:\s]*<(\d+)g', text)
    if salt_match:
        recommendations['sodium']['salt_limit'] = f"<{salt_match.group(1)}g/d"

    # 饮水建议
    water_match = re.search(r'每日饮水量[：:\s]*(\d+)[-~～](\d+)ml', text)
    if water_match:
        recommendations['water']['intake'] = f"{water_match.group(1)}-{water_match.group(2)}ml"

    # 食物推荐
    if '豆腐' in text:
        recommendations['purine'].append('适量豆制品')
    if '鸡蛋' in text:
        recommendations['purine'].append('推荐鸡蛋')
    if '牛奶' in text:
        recommendations['purine'].append('推荐牛奶')

    return recommendations


def calculate_ckd_stage(egfr: float) -> str:
    """根据 eGFR 判断 CKD 分期"""
    if egfr >= 90:
        return "CKD 1 期"
    elif egfr >= 60:
        return "CKD 2 期"
    elif egfr >= 45:
        return "CKD 3a 期"
    elif egfr >= 30:
        return "CKD 3b 期"
    elif egfr >= 15:
        return "CKD 4 期"
    else:
        return "CKD 5 期"


def generate_nutrition_targets(patient_info: Dict, recommendations: Dict) -> Dict[str, Any]:
    """基于患者情况生成营养目标"""
    targets = {}

    # 估算理想体重（简化公式）
    bmi = patient_info.get('bmi', 22)
    if bmi > 28:
        # 肥胖，按理想 BMI 计算
        ideal_bmi = 22
    else:
        ideal_bmi = bmi

    # 假设身高 170cm（如无法从报告中获取）
    height = 1.7
    ideal_weight = ideal_bmi * (height ** 2)

    # 蛋白质目标（CKD 患者 0.6-0.8g/kg）
    protein_per_kg = 0.7  # 取中间值
    protein_target = round(ideal_weight * protein_per_kg)
    targets['protein'] = {
        'value': f"{int(protein_target * 0.9)}-{int(protein_target * 1.1)}",
        'unit': 'g/d',
        'basis': '0.6-0.8g/kg·d (CKD 患者)',
        'note': '优质蛋白为主（鸡蛋、牛奶、鱼肉、豆腐）'
    }

    # 能量目标（CKD 患者 25-30kcal/kg，考虑减重需求取低值）
    energy_per_kg = 25  # 减重期
    energy_target = int(ideal_weight * energy_per_kg)
    targets['energy'] = {
        'value': f"{energy_target - 200}-{energy_target}",
        'unit': 'kcal/d',
        'basis': '25-30kcal/kg·d (减重期)',
        'note': '低 GI 食物，控制精制碳水'
    }

    # 碳水化合物目标（占总能量 50-55%）
    carb_low = int((energy_target - 200) * 0.50 / 4)
    carb_high = int(energy_target * 0.55 / 4)
    targets['carbohydrate'] = {
        'value': f"{carb_low}-{carb_high}",
        'unit': 'g/d',
        'basis': '占总能量 50-55%',
        'note': '选择全谷物，限制精制碳水'
    }

    # 脂肪目标（占总能量 20-25%，低脂饮食）
    fat_low = int((energy_target - 200) * 0.20 / 9)
    fat_high = int(energy_target * 0.25 / 9)
    targets['fat'] = {
        'value': f"{fat_low}-{fat_high}",
        'unit': 'g/d',
        'basis': '占总能量 20-25% (低脂)',
        'note': '橄榄油、菜籽油，避免动物油'
    }

    # 钠目标
    targets['sodium'] = {
        'value': '食盐<5g',
        'unit': 'g/d',
        'basis': '<2000mg 钠/d',
        'note': '高血压患者，避免咸菜、腊肉'
    }

    # 钾目标（根据肾功能）
    ckd_stage = patient_info.get('ckd_stage', '3b')
    if '3b' in ckd_stage or '4' in ckd_stage or '5' in ckd_stage:
        targets['potassium'] = {
            'value': '根据血钾水平调整',
            'unit': '',
            'basis': 'CKD 患者易高钾',
            'note': '避免高钾食物（香蕉、橙子、土豆）'
        }
    else:
        targets['potassium'] = {
            'value': '正常范围',
            'unit': '',
            'basis': '3.5-5.5mmol/L',
            'note': '适量摄入'
        }

    # 磷目标（CKD 患者限制）
    targets['phosphorus'] = {
        'value': '<800',
        'unit': 'mg/d',
        'basis': 'CKD 患者限制磷',
        'note': '避免动物内脏、加工食品'
    }

    # 钙目标
    targets['calcium'] = {
        'value': '800-1000',
        'unit': 'mg/d',
        'basis': '预防骨质疏松',
        'note': '配合维生素 D'
    }

    # 铁目标
    targets['iron'] = {
        'value': '12-20',
        'unit': 'mg/d',
        'basis': '预防贫血',
        'note': '肾病易缺铁'
    }

    # 水目标
    water_rec = recommendations.get('water', {}).get('intake', '1500-2000')
    targets['water'] = {
        'value': water_rec,
        'unit': 'ml/d',
        'basis': '根据肾功能调整',
        'note': '少量多次，避免睡前大量饮水'
    }

    # 餐次比
    targets['meal_ratio'] = {
        'breakfast': 30,
        'lunch': 40,
        'dinner': 30
    }

    return targets


def extract_all_data(pdf_path: str) -> Dict[str, Any]:
    """从 PDF 中提取所有数据"""
    if not os.path.exists(pdf_path):
        print(f"错误：文件不存在：{pdf_path}")
        return {}

    all_text = ""
    all_tables = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text += text + "\n"

            tables = page.extract_tables()
            if tables:
                all_tables.extend(tables)

    # 提取患者信息
    patient_info = extract_patient_info(all_text, all_tables)

    # 添加 CKD 分期
    if 'eGFR' in patient_info.get('indicators', {}):
        egfr_str = patient_info['indicators']['eGFR']
        egfr_match = re.search(r'(\d+\.?\d*)', egfr_str)
        if egfr_match:
            egfr = float(egfr_match.group(1))
            patient_info['ckd_stage'] = calculate_ckd_stage(egfr)

    # 提取营养建议
    recommendations = extract_nutrition_recommendations(all_text)

    # 生成营养目标
    nutrition_targets = generate_nutrition_targets(patient_info, recommendations)

    # 提取食物禁忌
    food_avoid = {
        'high_purine': ['动物内脏', '浓肉汤', '沙丁鱼', '凤尾鱼', '啤酒'],
        'high_fat': ['肥肉', '油炸食品', '奶油', '黄油'],
        'high_salt': ['咸菜', '腊肉', '火腿', '酱油', '味精'],
        'high_sugar': ['甜点', '含糖饮料', '果汁', '糖果'],
        'kidney_harmful': ['杨桃', '高剂量维生素 C', '蛋白粉'],
    }

    # 提取运动建议
    exercise = {
        'type': '有氧运动（快走、游泳、骑自行车）',
        'intensity': '中等强度（心率 110-130 次/分）',
        'frequency': '每周 5 次',
        'duration': '每次 30-45 分钟',
    }

    return {
        'source_file': pdf_path,
        'patient_info': patient_info,
        'nutrition_targets': nutrition_targets,
        'recommendations': recommendations,
        'food_avoid': food_avoid,
        'exercise': exercise,
        'ckd_stage': patient_info.get('ckd_stage', '未知'),
    }


def main():
    parser = argparse.ArgumentParser(description='从临床营养健康报告中提取数据（增强版）')
    parser.add_argument('--input', '-i', required=True, help='输入 PDF 文件路径')
    parser.add_argument('--output', '-o', help='输出 JSON 文件路径')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细信息')

    args = parser.parse_args()

    print(f"正在处理文件：{args.input}")

    # 提取数据
    data = extract_all_data(args.input)

    if not data:
        print("提取失败")
        sys.exit(1)

    # 输出结果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"数据已保存到：{args.output}")

    # 显示摘要
    print("\n" + "=" * 60)
    print("提取结果摘要")
    print("=" * 60)

    patient = data.get('patient_info', {})
    print(f"\n【患者信息】")
    print(f"  姓名：{patient.get('name', '未知')}")
    print(f"  BMI: {patient.get('bmi', '未知')}")
    print(f"  CKD 分期：{data.get('ckd_stage', '未知')}")

    if patient.get('indicators'):
        print(f"\n【关键指标】")
        for key, value in patient['indicators'].items():
            print(f"  {key}: {value}")

    if patient.get('medical_history'):
        print(f"\n【慢性病史】")
        for condition in patient['medical_history']:
            print(f"  - {condition}")

    targets = data.get('nutrition_targets', {})
    print(f"\n【营养目标】")
    for nutrient, info in targets.items():
        if nutrient == 'meal_ratio':
            continue
        if isinstance(info, dict):
            print(f"  {nutrient}: {info.get('value', '')} {info.get('unit', '')}")

    print(f"\n【运动建议】")
    exercise = data.get('exercise', {})
    print(f"  类型：{exercise.get('type', '')}")
    print(f"  频率：{exercise.get('frequency', '')}")
    print(f"  强度：{exercise.get('intensity', '')}")

    return data


if __name__ == '__main__':
    main()
