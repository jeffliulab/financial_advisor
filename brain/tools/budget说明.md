# Budget Planner Tool - 预算规划工具完整说明文档

## 📚 目录

- [模块功能](#模块功能)
- [数据存储](#数据存储)
- [数据结构](#数据结构)
- [Scope（有效范围）说明](#scope有效范围说明)
- [Time Type（时间类别）说明](#time-type时间类别说明)
- [计算规则](#计算规则)
- [月份筛选规则](#月份筛选规则)
- [公共接口（API）](#公共接口api)
- [程序流程图](#程序流程图)
- [使用示例](#使用示例)
- [注意事项](#注意事项)

---

## 模块功能

本脚本实现 budget_planner 工具的完整逻辑，包括：

- ✅ 获取用户 budget 信息
- ✅ 存入/删除 budget 项目到数据库
- ✅ 计算 dashboard 统计数据
- ✅ 按年份/月份筛选项目

---

## 数据存储

| 项目 | 说明 |
|------|------|
| **存储路径** | `data/users/{username}/budget.json` |
| **数据格式** | JSON |
| **用户隔离** | 每个用户独立的 budget 文件 |

---

## 数据结构

### 预算项目格式（单个 item）

```json
{
  "id": "item_20251024_123456_0",        // 唯一ID
  "name": "工资",                         // 项目名称
  "scope": "永久",                        // 有效范围（见下方说明）
  "time_type": "月度",                    // 时间类别："月度" 或 "非月度"
  "category": "收入",                     // 收支类别："收入" 或 "支出"
  "amount": 5000,                         // 金额（浮点数）
  "created_at": "2025-10-24T12:34:56"    // 创建时间
}
```

### 预算数据文件格式（budget.json）

```json
{
  "items": [
    {item1},
    {item2},
    ...
  ]
}
```

---

## Scope（有效范围）说明

### Scope 的三种格式

#### 1. "永久"
- **说明**：在所有年份都有效
- **示例**：每月工资、房租等固定收支

#### 2. "2025年"
- **说明**：只在指定年份有效，不限定具体月份
- **示例**：2025年的年度项目

#### 3. "2025年12月"
- **说明**：只在指定年份的指定月份有效
- **示例**：12月的旅行、年终奖等

### Scope 解析规则表

| Scope | 年份判断 | 月份判断 | 计算规则 |
|-------|----------|----------|----------|
| "永久" | 任何年份匹配 | 任何月份显示 | 月度×12+非月度 |
| "2025年" | 只匹配2025 | 所有月份显示 | 月度×12+非月度 |
| "2025年12月" | 只匹配2025 | 只显示12月 | 月度×12+非月度 |

---

## Time Type（时间类别）说明

### 1. "月度"
- **特点**：每个月都会发生的项目
- **年度计算**：自动 × 12
- **月份筛选**：总是显示（不受筛选影响）
- **示例**：工资、房租、水电费

### 2. "非月度"
- **特点**：一次性或不定期的项目
- **年度计算**：按实际金额
- **月份筛选**：根据 scope 中的月份决定是否显示
- **示例**：旅行、购买电器、年终奖

---

## 计算规则

### Dashboard 年度统计计算逻辑

1. **月度收入总额** = Σ(所有"月度"+"收入"项目的金额)
2. **月度支出总额** = Σ(所有"月度"+"支出"项目的金额)
3. **非月度收入总额** = Σ(所有"非月度"+"收入"项目的金额)
4. **非月度支出总额** = Σ(所有"非月度"+"支出"项目的金额)

5. **年度总收入** = (月度收入总额 × 12) + 非月度收入总额
6. **年度总支出** = (月度支出总额 × 12) + 非月度支出总额
7. **年度总盈余** = 年度总收入 - 年度总支出

### 计算示例

假设2025年有以下项目：
- 工资(月度收入): 5000
- 房租(月度支出): 2000
- 旅行(非月度支出, 12月): 5000
- 年终奖(非月度收入, 12月): 10000

**计算过程：**
```
年度总收入 = (5000 × 12) + 10000 = 70000
年度总支出 = (2000 × 12) + 5000 = 29000
年度总盈余 = 70000 - 29000 = 41000
```

---

## 月份筛选规则

### 当用户选择特定月份时（如只选择12月）

#### 1. "月度"项目
- ✅ 总是显示（不受月份筛选影响）
- **原因**：月度项目每个月都存在

#### 2. "非月度"项目
- 根据 scope 中的月份判断

### 判断流程

```
┌─────────────────────────────────────┐
│ scope 包含具体月份？                 │
└──────────┬──────────────────────────┘
           │
     ┌─────┴─────┐
     │           │
   是("2025年12月") 否("2025年"或"永久")
     │           │
     ↓           ↓
检查月份是否     总是显示
在筛选范围内    （无具体月份限制）
     │
 ┌───┴───┐
 │       │
是      否
 │       │
显示    不显示
```

### 筛选示例

**选择月份 = [12]**

| 项目 | Scope | Time Type | 是否显示 | 原因 |
|------|-------|-----------|----------|------|
| 工资 | 永久 | 月度 | ✅ 显示 | 月度项目总是显示 |
| 房租 | 永久 | 月度 | ✅ 显示 | 月度项目总是显示 |
| 旅行 | 2025年12月 | 非月度 | ✅ 显示 | 12月在筛选中 |
| 聚餐 | 2025年8月 | 非月度 | ❌ 不显示 | 8月不在筛选中 |
| 年终奖 | 2025年 | 非月度 | ✅ 显示 | 无具体月份 |

---

## 公共接口（API）

### 1. get_user_budget_info(username, year=None)

**功能**: 获取用户的预算信息

**参数**:
- `username` (str): 用户名
- `year` (int, optional): 年份（可选），不指定则返回所有年份

**返回**:
```python
{
  "items": [...],                      # 项目列表
  "available_years": [2024, 2025, ...]  # 可用年份
}
```

---

### 2. add_budget_item(username, item)

**功能**: 添加一个预算项目

**参数**:
- `username` (str): 用户名
- `item` (dict): 项目数据字典（见数据结构）

**返回**:
```python
{
  "success": bool,
  "message": str,
  "item_id": str
}
```

---

### 3. delete_budget_item(username, item_id)

**功能**: 删除一个预算项目

**参数**:
- `username` (str): 用户名
- `item_id` (str): 项目ID

**返回**:
```python
{
  "success": bool,
  "message": str
}
```

---

### 4. calculate_dashboard(username, year)

**功能**: 计算指定年份的Dashboard统计数据

**参数**:
- `username` (str): 用户名
- `year` (int): 年份

**返回**:
```python
{
  "year": int,
  "total_income": float,          # 年度总收入
  "total_expense": float,         # 年度总支出
  "total_surplus": float,         # 年度总盈余
  "monthly_income": float,        # 月度收入（单月）
  "monthly_expense": float,       # 月度支出（单月）
  "non_monthly_income": float,    # 非月度收入总和
  "non_monthly_expense": float    # 非月度支出总和
}
```

---

### 5. get_items_by_month(username, year, months=None)

**功能**: 获取指定年份和月份的项目

**参数**:
- `username` (str): 用户名
- `year` (int): 年份
- `months` (list, optional): 月份列表（1-12），None表示所有月份

**返回**:
```python
{
  "income_items": [...],   # 收入项目列表
  "expense_items": [...]   # 支出项目列表
}
```

---

## 程序流程图

### 添加项目流程

```
用户调用 add_budget_item(username, item)
    │
    ├─ 验证必填字段（name, scope, time_type, category, amount）
    │   └─ 缺少字段？→ 返回错误
    │
    ├─ 验证 category（必须是"收入"或"支出"）
    │   └─ 不合法？→ 返回错误
    │
    ├─ 验证 time_type（必须是"月度"或"非月度"）
    │   └─ 不合法？→ 返回错误
    │
    ├─ 验证 amount（必须是非负数字）
    │   └─ 不合法？→ 返回错误
    │
    ├─ 加载现有 budget 数据
    │
    ├─ 生成唯一 ID 和时间戳
    │
    ├─ 添加项目到列表
    │
    ├─ 保存到 JSON 文件
    │
    └─ 返回成功结果
```

---

### 获取项目列表流程

```
用户调用 get_items_by_month(username, year, months)
    │
    ├─ 调用 get_user_budget_info(username, year)
    │   │
    │   ├─ 加载 budget.json
    │   │
    │   ├─ 提取所有可用年份
    │   │   ├─ scope == "永久" → 添加范围年份
    │   │   └─ scope 包含"年" → 提取年份数字
    │   │
    │   └─ 如果指定年份，过滤项目
    │       ├─ scope == "永久" → 包含
    │       └─ scope.startswith(f"{year}年") → 包含
    │
    ├─ 遍历所有项目
    │   │
    │   ├─ 项目是"月度"？
    │   │   └─ 是 → 总是包含（include_item = True）
    │   │
    │   └─ 项目是"非月度"？
    │       │
    │       ├─ months == None？
    │       │   └─ 是 → 总是包含
    │       │
    │       └─ 否 → 检查 scope 中的月份
    │           │
    │           ├─ scope 包含"月"？
    │           │   ├─ 是 → 提取月份数字
    │           │   │       └─ 月份在筛选范围？
    │           │   │           ├─ 是 → 包含
    │           │   │           └─ 否 → 不包含
    │           │   └─ 否 → 总是包含（无具体月份）
    │           │
    │           └─ 解析失败？→ 总是包含（宽容处理）
    │
    ├─ 按 category 分类
    │   ├─ "收入" → income_items
    │   └─ "支出" → expense_items
    │
    └─ 返回 {income_items, expense_items}
```

---

### Dashboard计算流程

```
用户调用 calculate_dashboard(username, year)
    │
    ├─ 获取指定年份的所有项目
    │
    ├─ 初始化统计变量
    │   ├─ monthly_income = 0
    │   ├─ monthly_expense = 0
    │   ├─ non_monthly_income = 0
    │   └─ non_monthly_expense = 0
    │
    ├─ 遍历所有项目
    │   │
    │   ├─ time_type == "月度" 且 category == "收入"
    │   │   └─ monthly_income += amount
    │   │
    │   ├─ time_type == "月度" 且 category == "支出"
    │   │   └─ monthly_expense += amount
    │   │
    │   ├─ time_type == "非月度" 且 category == "收入"
    │   │   └─ non_monthly_income += amount
    │   │
    │   └─ time_type == "非月度" 且 category == "支出"
    │       └─ non_monthly_expense += amount
    │
    ├─ 计算年度总计
    │   ├─ total_income = (monthly_income × 12) + non_monthly_income
    │   ├─ total_expense = (monthly_expense × 12) + non_monthly_expense
    │   └─ total_surplus = total_income - total_expense
    │
    └─ 返回统计结果
```

---

### 删除项目流程

```
用户调用 delete_budget_item(username, item_id)
    │
    ├─ 加载 budget 数据
    │
    ├─ 过滤掉指定 ID 的项目
    │   └─ items = [item for item in items if item.id != item_id]
    │
    ├─ 检查是否成功删除
    │   ├─ 列表长度未变？→ 返回错误（未找到）
    │   └─ 列表长度减少？→ 继续
    │
    ├─ 保存到 JSON 文件
    │
    └─ 返回成功结果
```

---

## 使用示例

### 示例1: 添加月度收入项目

```python
item = {
    "name": "工资",
    "scope": "永久",
    "time_type": "月度",
    "category": "收入",
    "amount": 5000
}
result = add_budget_item("admin", item)
# 返回: {"success": True, "message": "项目添加成功", "item_id": "item_..."}
```

---

### 示例2: 添加非月度支出项目

```python
item = {
    "name": "夏威夷旅行",
    "scope": "2025年12月",
    "time_type": "非月度",
    "category": "支出",
    "amount": 5000
}
result = add_budget_item("admin", item)
```

---

### 示例3: 获取2025年的Dashboard统计

```python
dashboard = calculate_dashboard("admin", 2025)
# 返回:
# {
#     "year": 2025,
#     "total_income": 70000,
#     "total_expense": 29000,
#     "total_surplus": 41000,
#     "monthly_income": 5000,
#     "monthly_expense": 2000,
#     "non_monthly_income": 10000,
#     "non_monthly_expense": 5000
# }
```

---

### 示例4: 获取12月的所有项目

```python
items = get_items_by_month("admin", 2025, [12])
# 返回:
# {
#     "income_items": [...],  # 包含月度项目 + 12月的非月度项目
#     "expense_items": [...]
# }
```

---

### 示例5: 删除项目

```python
result = delete_budget_item("admin", "item_20251024_123456_0")
# 返回: {"success": True, "message": "项目删除成功"}
```

---

## 注意事项

### 1. 数据持久化
- 所有数据存储在 JSON 文件中
- 自动创建用户目录
- 文件编码使用 UTF-8

### 2. 用户隔离
- 每个用户有独立的 `budget.json`
- 数据完全隔离，互不影响

### 3. 错误处理
- 所有公共函数都有完整的错误处理
- 验证失败返回详细的错误信息
- 文件操作异常会被捕获

### 4. ID生成规则
- **格式**: `item_{日期时间}_{序号}`
- **唯一性**: 使用时间戳 + 当前项目数量
- **示例**: `item_20251024_123456_0`

### 5. 扩展性
- 易于添加新的统计维度
- 可以方便地添加新的过滤条件
- 数据结构支持未来扩展

---

## 文件位置

- **模块文件**: `brain/tools/budget_planner.py`
- **文档文件**: `brain/tools/budget说明.md`
- **测试文件**: `server/tools_test/budget_test.py`
- **前端界面**: `web/tools/budget-planner.html`
- **API接口**: `server/main.py` (Budget Planner API 部分)

---

**最后更新**: 2025-10-24  
**版本**: 1.0.0


