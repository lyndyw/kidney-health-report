# 营养数据提取规则

本文档详细说明从营养报告 PDF/图片中提取营养数据的规则和映射关系。

## 提取流程

```
输入文件 (PDF/图片)
    ↓
判断文件类型
    ├── 文字版 PDF → pdfplumber 提取
    └── 扫描版/图片 → OCR 提取
    ↓
文本预处理
    ↓
关键词匹配 + 正则提取
    ↓
数据验证和标准化
    ↓
输出 JSON 数据
```

## 营养素关键词映射表

### 能量类
| 中文关键词 | 英文关键词 | 单位 | 备注 |
|-----------|-----------|------|------|
| 能量 | Energy | kcal/kJ | |
| 热量 | Energy intake | 千卡/千焦 | |
| 总能量 | Total energy | 大卡 | |
| 热能 | Calorie | | |

### 宏量营养素
| 中文关键词 | 英文关键词 | 单位 | 备注 |
|-----------|-----------|------|------|
| 蛋白质 | Protein | g | |
| 优质蛋白 | High-quality protein | g | |
| 碳水化合物 | Carbohydrate | g | |
| 碳水 | Carbs | g | 简称 |
| 脂肪 | Fat | g | |
| 总脂肪 | Total fat | g | |
| 脂类 | Lipid | g | |

### 矿物质
| 中文关键词 | 英文关键词 | 单位 | 备注 |
|-----------|-----------|------|------|
| 钠 | Sodium, Na | mg | |
| 钠盐 | Sodium salt | mg | |
| 钾 | Potassium, K | mg | |
| 磷 | Phosphorus, P | mg | |
| 钙 | Calcium, Ca | mg | |
| 铁 | Iron, Fe | mg | |
| 锌 | Zinc, Zn | mg | |
| 镁 | Magnesium, Mg | mg | |

### 其他营养素
| 中文关键词 | 英文关键词 | 单位 | 备注 |
|-----------|-----------|------|------|
| 膳食纤维 | Dietary fiber | g | |
| 纤维 | Fiber | g | 简称 |
| 胆固醇 | Cholesterol | mg | |
| 维生素 A | Vitamin A, VA | μgRE | |
| 维生素 C | Vitamin C, VC | mg | |
| 维生素 D | Vitamin D, VD | μg | |
| 维生素 E | Vitamin E, VE | mgα-TE | |

### 水分
| 中文关键词 | 英文关键词 | 单位 | 备注 |
|-----------|-----------|------|------|
| 水 | Water | ml | |
| 水分 | Moisture | ml | |
| 饮水量 | Fluid intake | ml | |
| 摄入量 | Intake | ml | |

## 提取模式

### 模式 1：键值对格式
```
能量：1800kcal
蛋白质：65g
脂肪：50g
```

正则表达式：
```regex
(能量 | 蛋白质 | 脂肪)[:：\s]*(\d+(?:\.\d+)?)\s*(kcal|g|mg)?
```

### 模式 2：表格格式
| 项目 | 摄入量 | 单位 |
|------|--------|------|
| 能量 | 1800 | kcal |

提取逻辑：识别表格结构，定位关键词所在行，提取对应列数值。

### 模式 3：句子格式
```
每日能量摄入约为 1800-2000 千卡，蛋白质 60-70 克。
```

正则表达式：
```regex
(能量 | 蛋白质)[^0-9]*(\d+(?:\.\d+)?)[^0-9]*(kcal|千卡 | g|克)
```

## 数值处理规则

### 范围值处理
- 输入：`1800-2000kcal` 或 `1800~2000kcal`
- 处理：取平均值 `(1800+2000)/2 = 1900`
- 输出：`{"value": 1900, "unit": "kcal", "raw": "1800-2000kcal"}`

### 单位转换
| 原单位 | 目标单位 | 转换系数 |
|--------|----------|----------|
| kJ | kcal | ÷ 4.184 |
| 千焦 | 千卡 | ÷ 4.184 |
| mg | g | ÷ 1000 |
| μg | mg | ÷ 1000 |

### 餐次比提取
格式识别：
- `早餐 30%/午餐 40%/晚餐 30%`
- `早：30% 中：40% 晚：30%`
- `早餐比例 30%，午餐 40%，晚餐 30%`

正则表达式：
```regex
早餐 [:：\s]*(\d+)%?[:：\s/]*午餐 [:：\s]*(\d+)%?[:：\s/]*晚餐 [:：\s]*(\d+)%?
```

## 数据验证

### 合理性检查
| 营养素 | 合理范围 | 超出处理 |
|--------|----------|----------|
| 能量 | 800-4000 kcal | 标记警告 |
| 蛋白质 | 20-200 g | 标记警告 |
| 脂肪 | 20-200 g | 标记警告 |
| 碳水化合物 | 100-600 g | 标记警告 |
| 钠 | 500-10000 mg | 标记警告 |

### 缺失数据处理
如某项营养素未提取到：
1. 尝试同义词再次匹配
2. 使用默认值（根据患者体重计算）
3. 标记为"需人工补充"

## 肾病患者营养特点

### 蛋白质
- CKD 非透析患者：0.6-0.8 g/kg·d
- 透析患者：1.0-1.2 g/kg·d
- 优质蛋白比例：≥50%

### 能量
- 维持体重：25-30 kcal/kg·d
- 减重：减少 500 kcal/d
- 营养不良：增加至 30-35 kcal/kg·d

### 钠
- 一般患者：<2000 mg/d (食盐<5g)
- 高血压/水肿：<1500 mg/d (食盐<3g)

### 钾
- 血钾正常：不限
- 高钾血症：<2000 mg/d

### 磷
- CKD 3-5 期：<800 mg/d
- 透析患者：<1000 mg/d

## 示例

### 示例 1：文字版 PDF 提取
**输入文本**：
```
营养评估报告

姓名：张三
每日营养摄入量：
能量：1850 kcal
蛋白质：72 g
脂肪：55 g
碳水化合物：280 g
钠：1800 mg
钾：2500 mg
钙：600 mg
```

**提取结果**：
```json
{
  "energy": {"value": 1850, "unit": "kcal", "raw": "1850 kcal"},
  "protein": {"value": 72, "unit": "g", "raw": "72 g"},
  "fat": {"value": 55, "unit": "g", "raw": "55 g"},
  "carbohydrate": {"value": 280, "unit": "g", "raw": "280 g"},
  "sodium": {"value": 1800, "unit": "mg", "raw": "1800 mg"},
  "potassium": {"value": 2500, "unit": "mg", "raw": "2500 mg"},
  "calcium": {"value": 600, "unit": "mg", "raw": "600 mg"}
}
```

### 示例 2：表格格式提取
**输入表格**：
| 营养素 | 摄入量 | 单位 |
|--------|--------|------|
| 总能量 | 1650 | 千卡 |
| 蛋白质 | 58.5 | 克 |
| 脂肪 | 48.2 | 克 |

**提取结果**：
```json
{
  "energy": {"value": 1650, "unit": "kcal", "raw": "1650 千卡"},
  "protein": {"value": 58.5, "unit": "g", "raw": "58.5 克"},
  "fat": {"value": 48.2, "unit": "g", "raw": "48.2 克"}
}
```

## 常见问题处理

### 问题 1：扫描版 PDF 无法提取文字
**解决**：使用 OCR 处理
```bash
# 确保安装 Tesseract OCR
brew install tesseract  # macOS
apt-get install tesseract-ocr  # Linux

# 安装 Python 库
pip install pytesseract pdf2image
```

### 问题 2：提取数值异常
**解决**：检查单位是否正确，进行单位转换
```python
if unit == 'kJ':
    value = value / 4.184  # 转为 kcal
    unit = 'kcal'
```

### 问题 3：关键词匹配失败
**解决**：扩展关键词库，添加同义词
```python
NUTRITION_KEYWORDS['protein'].extend(['蛋白粉', 'Pro'])
```

## 输出格式

完整 JSON 输出示例：
```json
{
  "source_file": "/path/to/report.pdf",
  "energy": {"value": 1800, "unit": "kcal", "raw": "1800kcal"},
  "protein": {"value": 65, "unit": "g", "raw": "65g"},
  "carbohydrate": {"value": 250, "unit": "g", "raw": "250g"},
  "fat": {"value": 55, "unit": "g", "raw": "55g"},
  "sodium": {"value": 1500, "unit": "mg", "raw": "1500mg"},
  "potassium": {"value": 2000, "unit": "mg", "raw": "2000mg"},
  "phosphorus": {"value": 800, "unit": "mg", "raw": "800mg"},
  "calcium": {"value": 700, "unit": "mg", "raw": "700mg"},
  "iron": {"value": 15, "unit": "mg", "raw": "15mg"},
  "water": {"value": 1500, "unit": "ml", "raw": "1500ml"},
  "meal_ratio": {
    "breakfast": 30,
    "lunch": 40,
    "dinner": 30
  }
}
```
