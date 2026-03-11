#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本 - 验证报告生成功能

使用方法:
    python3 test_report_generation.py
"""

import os
import sys
from datetime import datetime

# 添加脚本目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from generate_report import generate_report, calculate_bmi


def test_bmi_calculation():
    """测试 BMI 计算"""
    print("=== 测试 BMI 计算 ===")

    test_cases = [
        (45, 160, "体重过低"),  # BMI=17.6
        (60, 170, "正常范围"),  # BMI=20.8
        (75, 170, "超重"),      # BMI=26.0
        (90, 170, "肥胖"),      # BMI=31.1
    ]

    all_passed = True
    for weight, height, expected_level in test_cases:
        bmi, level = calculate_bmi(weight, height)
        passed = level == expected_level
        status = "✓" if passed else "✗"
        print(f"{status} 体重={weight}kg, 身高={height}cm → BMI={bmi}, 等级={level} (期望：{expected_level})")
        if not passed:
            all_passed = False

    print()
    return all_passed


def test_report_generation():
    """测试报告生成"""
    print("=== 测试报告生成 ===")

    # 测试数据
    patient = {
        'name': '测试患者',
        'age': 55,
        'gender': '男',
        'height': 170,
        'weight': 68,
        'waist': 85,
        'habits': '不抽烟，偶尔饮酒，睡眠一般',
        'diet_status': '口味偏咸，蔬菜水果摄入不足',
        'medical_history': '高血压、糖尿病',
        'indicators': '肌酐 125μmol/L、空腹血糖 7.2mmol/L、血压 145/90mmHg',
        'problems': '体重超标，血压控制不佳，血糖波动',
    }

    nutrition_data = {
        'energy': {'value': 1800, 'unit': 'kcal', 'raw': '1800kcal'},
        'protein': {'value': 65, 'unit': 'g', 'raw': '65g'},
        'carbohydrate': {'value': 280, 'unit': 'g', 'raw': '280g'},
        'fat': {'value': 55, 'unit': 'g', 'raw': '55g'},
        'sodium': {'value': 2200, 'unit': 'mg', 'raw': '2200mg'},
        'potassium': {'value': 2500, 'unit': 'mg', 'raw': '2500mg'},
        'meal_ratio': {'breakfast': 30, 'lunch': 40, 'dinner': 30},
    }

    period = {
        'start': '2026-03-15',
        'end': '2026-04-15',
    }

    manager = {
        'name': '李营养师',
        'date': '2026-03-11',
    }

    # 生成报告
    output_path = os.path.join(os.path.dirname(script_dir), 'test_output', '测试报告.docx')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        result_path = generate_report(
            patient=patient,
            nutrition_data=nutrition_data,
            period=period,
            manager=manager,
            output_path=output_path,
            organization='测试医疗机构',
        )
        print(f"✓ 报告生成成功：{result_path}")
        print(f"  文件大小：{os.path.getsize(result_path) / 1024:.1f} KB")
        return True
    except Exception as e:
        print(f"✗ 报告生成失败：{e}")
        return False


def test_nutrition_extraction():
    """测试营养数据提取（需要有测试文件）"""
    print("=== 测试营养数据提取 ===")

    extract_script = os.path.join(script_dir, 'extract_nutrition_data.py')

    # 检查是否有测试文件
    test_files = [
        '/tmp/test_nutrition.pdf',
        '/tmp/test_nutrition.jpg',
    ]

    found_file = None
    for test_file in test_files:
        if os.path.exists(test_file):
            found_file = test_file
            break

    if not found_file:
        print("⊘ 跳过测试 - 未找到测试文件")
        print("  提示：将测试 PDF 或图片放在 /tmp/test_nutrition.pdf")
        return True

    try:
        import subprocess
        result = subprocess.run(
            ['python3', extract_script, '-i', found_file, '-v'],
            capture_output=True,
            text=True,
            timeout=30,
        )
        print(result.stdout)
        if result.returncode == 0:
            print("✓ 营养数据提取成功")
            return True
        else:
            print(f"✗ 营养数据提取失败：{result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("✗ 提取超时")
        return False
    except Exception as e:
        print(f"✗ 测试失败：{e}")
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("肾病患者健康生活方式建议报告技能 - 功能测试")
    print("=" * 60)
    print()

    results = {
        'BMI 计算': test_bmi_calculation(),
        '报告生成': test_report_generation(),
        '营养提取': test_nutrition_extraction(),
    }

    print()
    print("=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print()
    print(f"总计：{passed}/{total} 测试通过")

    if passed == total:
        print("🎉 所有测试通过！技能可以正常使用。")
    else:
        print("⚠️ 部分测试失败，请检查相关功能。")

    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
