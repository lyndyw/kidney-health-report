# 肾病患者健康生活方式建议报告技能

## 快速开始

### 1. 安装依赖

```bash
# PDF 处理
pip install pdfplumber pypdf python-docx

# OCR（处理扫描版 PDF/图片）
pip install pytesseract pdf2image Pillow

# macOS 还需要安装 Tesseract OCR 引擎
brew install tesseract poppler

# Linux
apt-get install tesseract-ocr poppler-utils
```

### 2. 使用方式

#### 方式一：直接对话

只需提供以下信息，我会自动生成完整报告：

```
【患者基本信息】
- 姓名：张三
- 年龄：55
- 性别：男
- 身高：170cm
- 体重：68kg
- 腰围：85cm
- 生活习惯：不抽烟，偶尔饮酒，睡眠一般
- 饮食现状：口味偏咸，蔬菜水果摄入不足
- 既往史：高血压、糖尿病
- 检查指标：肌酐 125μmol/L、空腹血糖 7.2mmol/L

【营养报告文件】
- 文件路径：/path/to/nutrition_report.pdf

【核心问题】
- 问题 1：体重超标
- 问题 2：血压控制不佳

【干预周期】
- 开始日期：2026-03-15
- 结束日期：2026-04-15

【健管师信息】
- 姓名：李营养师
- 干预日期：2026-03-11
```

#### 方式二：命令行

```bash
python3 "$SKILLS_ROOT/kidney-health-report/scripts/generate_report.py" \
  --name "张三" \
  --age 55 \
  --gender "男" \
  --height 170 \
  --weight 68 \
  --waist 85 \
  --habits "不抽烟，偶尔饮酒，睡眠一般" \
  --diet-status "口味偏咸，蔬菜水果摄入不足" \
  --medical-history "高血压、糖尿病" \
  --indicators "肌酐 125μmol/L、空腹血糖 7.2mmol/L" \
  --problems "体重超标，血压控制不佳" \
  --nutrition-report "/path/to/nutrition_report.pdf" \
  --start-date "2026-03-15" \
  --end-date "2026-04-15" \
  --manager-name "李营养师" \
  --output "/Users/liyn/Downloads/张三_健康报告.docx"
```

#### 方式三：分步处理

第一步：提取营养数据
```bash
python3 "$SKILLS_ROOT/kidney-health-report/scripts/extract_nutrition_data.py" \
  -i /path/to/nutrition_report.pdf \
  -o /tmp/nutrition_data.json
```

第二步：生成报告
```bash
python3 "$SKILLS_ROOT/kidney-health-report/scripts/generate_report.py" \
  --name "张三" \
  --age 55 \
  ... \
  --nutrition-data /tmp/nutrition_data.json \
  --output report.docx
```

### 3. 测试技能

```bash
python3 "$SKILLS_ROOT/kidney-health-report/scripts/test_report_generation.py"
```

## 文件结构

```
kidney-health-report/
├── SKILL.md                              # 技能主文件
├── scripts/
│   ├── extract_nutrition_data.py         # 营养数据提取
│   ├── generate_report.py                # 报告生成
│   └── test_report_generation.py         # 测试脚本
├── references/
│   └── nutrition_extraction_guide.md     # 营养提取规则
└── templates/
    └── (可选的 Word 模板)
```

## 输出报告格式

报告包含以下部分：

1. **基本信息** - 6 列表格，含 BMI 计算和体型判断
2. **问题和管理目标** - 3 列表格，列出核心问题和管理目标
3. **营养干预方案**
   - 3.1 营养干预原则
   - 3.2 营养干预具体方案（5 列表格）
   - 3.3 第一周详细计划
4. **运动方案** - FITTVP 原则表格
5. **心理与睡眠建议** - 编号列表
6. **总结和关键提醒** - 编号列表 + 健管师署名

## 营养数据提取

支持的输入格式：
- PDF（文字版）- 使用 pdfplumber 提取
- PDF（扫描版）- 使用 OCR 提取
- 图片（JPG/PNG）- 使用 OCR 提取

提取的营养素：
- 能量、蛋白质、碳水化合物、脂肪
- 钠、钾、磷、钙、铁
- 水分、膳食纤维
- 餐次比例

## 肾病营养原则

| 营养素 | 推荐标准 | 说明 |
|--------|----------|------|
| 蛋白质 | 0.6-0.8g/kg·d | CKD 患者优质低蛋白 |
| 能量 | 25-30kcal/kg·d | 维持理想体重 |
| 盐 | <5g/d | 高血压患者<3g/d |
| 钾 | 视血钾水平 | 高钾血症需限钾 |
| 磷 | <800mg/d | 限制高磷食物 |

## 常见问题

### Q: OCR 提取不准确怎么办？
A: 确保图片清晰，分辨率至少 300 DPI。如是 PDF，优先使用文字版。

### Q: 营养数据提取不完整怎么办？
A: 检查报告格式，手动补充缺失数据。可参考 `references/nutrition_extraction_guide.md` 添加关键词。

### Q: 如何修改报告格式？
A: 编辑 `generate_report.py` 中的表格生成函数，或修改 `SKILL.md` 中的格式说明。

## 技术支持

如遇到问题：
1. 检查依赖是否安装完整
2. 运行测试脚本验证功能
3. 查看 `references/nutrition_extraction_guide.md` 了解提取规则
4. 联系技能开发者

## 版本历史

- v1.0.0 (2026-03-11) - 初始版本
  - 支持 PDF/图片营养报告提取
  - 生成 Word 格式健康建议报告
  - 包含完整的 5 部分报告结构
