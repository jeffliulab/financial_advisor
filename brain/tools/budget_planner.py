"""
Budget Planner Tool - 预算规划工具

本模块实现完整的预算规划功能，包括：
- 获取/存储/删除用户预算项目
- 计算Dashboard统计数据  
- 按年份/月份筛选项目

数据存储: data/users/{username}/budget.json

详细文档请参见: brain/tools/budget说明.md
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class BudgetPlanner:
    """预算规划工具类"""
    
    def __init__(self, data_dir: str = "data"):
        """
        初始化预算规划工具
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = Path(data_dir)
        
    def _get_user_budget_file(self, username: str) -> Path:
        """
        获取用户的budget数据文件路径
        
        Args:
            username: 用户名
            
        Returns:
            Path: budget文件路径
        """
        user_dir = self.data_dir / "users" / username
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir / "budget.json"
    
    def _load_budget(self, username: str) -> Dict:
        """
        加载用户的budget数据
        
        Args:
            username: 用户名
            
        Returns:
            Dict: budget数据
        """
        budget_file = self._get_user_budget_file(username)
        
        if not budget_file.exists():
            # 初始化空的budget数据
            return {"items": []}
        
        with open(budget_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_budget(self, username: str, budget_data: Dict):
        """
        保存用户的budget数据
        
        Args:
            username: 用户名
            budget_data: budget数据
        """
        budget_file = self._get_user_budget_file(username)
        
        with open(budget_file, 'w', encoding='utf-8') as f:
            json.dump(budget_data, f, ensure_ascii=False, indent=2)
    
    def get_user_budget_info(self, username: str, year: Optional[int] = None) -> Dict:
        """
        获取用户的budget内容和信息
        
        Args:
            username: 用户名
            year: 年份（可选），不指定则返回所有年份
            
        Returns:
            Dict: budget信息
                {
                    "items": [...],
                    "available_years": [2024, 2025, ...]
                }
        """
        budget_data = self._load_budget(username)
        items = budget_data.get("items", [])
        
        # 获取所有可用的年份
        available_years = set()
        for item in items:
            scope = item.get("scope", "")
            if scope == "永久":
                # 永久项目在所有年份都有效
                if not year:
                    available_years.update(range(2020, datetime.now().year + 10))
            elif "年" in scope:
                # 格式: "2025年12月" 或 "2025年"
                year_part = scope.split("年")[0]
                try:
                    available_years.add(int(year_part))
                except ValueError:
                    pass
        
        available_years = sorted(list(available_years))
        
        # 如果指定了年份，过滤项目
        if year:
            filtered_items = []
            for item in items:
                scope = item.get("scope", "")
                if scope == "永久":
                    filtered_items.append(item)
                elif scope.startswith(f"{year}年"):
                    filtered_items.append(item)
            items = filtered_items
        
        return {
            "items": items,
            "available_years": available_years
        }
    
    def add_budget_item(self, username: str, item: Dict) -> Dict:
        """
        添加一个budget项目
        
        Args:
            username: 用户名
            item: 项目数据
                {
                    "name": "项目名称",
                    "scope": "有效范围",  # 如: "永久", "2025年12月", "2025年"
                    "time_type": "时间类别",  # "月度" 或 "非月度"
                    "category": "收支类别",  # "收入" 或 "支出"
                    "amount": 金额
                }
                
        Returns:
            Dict: 操作结果
                {
                    "success": bool,
                    "message": str,
                    "item_id": str
                }
        """
        # 验证必填字段
        required_fields = ["name", "scope", "time_type", "category", "amount"]
        for field in required_fields:
            if field not in item:
                return {
                    "success": False,
                    "message": f"缺少必填字段: {field}",
                    "item_id": None
                }
        
        # 标准化 scope（支持英文）
        scope = item["scope"]
        if scope in ["Permanent", "permanent", "永久"]:
            item["scope"] = "永久"
        # 如果是英文格式的年月，转换为中文
        elif "Year" in scope or "year" in scope:
            # 例如: "2025 Year 12 Month" -> "2025年12月"
            import re
            year_match = re.search(r'(\d{4})', scope)
            month_match = re.search(r'Month\s*(\d{1,2})|(\d{1,2})\s*Month', scope, re.IGNORECASE)
            if year_match:
                year = year_match.group(1)
                if month_match:
                    month = month_match.group(1) or month_match.group(2)
                    item["scope"] = f"{year}年{month}月"
                else:
                    item["scope"] = f"{year}年"
        
        # 验证收支类别
        valid_categories = ["收入", "支出", "Income", "Expense"]
        if item["category"] not in valid_categories:
            return {
                "success": False,
                "message": "收支类别必须是'收入'/'Income'或'支出'/'Expense'",
                "item_id": None
            }
        
        # 标准化为中文
        if item["category"] in ["Income", "income"]:
            item["category"] = "收入"
        elif item["category"] in ["Expense", "expense"]:
            item["category"] = "支出"
        
        # 验证时间类别
        valid_time_types = ["月度", "非月度", "Monthly", "monthly", "One-time", "one-time"]
        if item["time_type"] not in valid_time_types:
            return {
                "success": False,
                "message": "时间类别必须是'月度'/'Monthly'或'非月度'/'One-time'",
                "item_id": None
            }
        
        # 标准化为中文
        if item["time_type"] in ["Monthly", "monthly"]:
            item["time_type"] = "月度"
        elif item["time_type"] in ["One-time", "one-time", "onetime"]:
            item["time_type"] = "非月度"
        
        # 验证金额
        try:
            amount = float(item["amount"])
            if amount < 0:
                return {
                    "success": False,
                    "message": "金额不能为负数",
                    "item_id": None
                }
        except (ValueError, TypeError):
            return {
                "success": False,
                "message": "金额必须是数字",
                "item_id": None
            }
        
        # 加载现有数据
        budget_data = self._load_budget(username)
        
        # 生成唯一ID
        item_id = f"item_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(budget_data['items'])}"
        item["id"] = item_id
        item["created_at"] = datetime.now().isoformat()
        
        # 添加项目
        budget_data["items"].append(item)
        
        # 保存数据
        self._save_budget(username, budget_data)
        
        return {
            "success": True,
            "message": "项目添加成功",
            "item_id": item_id
        }
    
    def update_budget_item(self, username: str, item_id: str, updates: Dict) -> Dict:
        """
        更新一个budget项目
        
        Args:
            username: 用户名
            item_id: 项目ID
            updates: 更新的数据
                {
                    "name": "项目名称" (可选),
                    "scope": "有效范围" (可选),
                    "time_type": "时间类别" (可选),
                    "category": "收支类别" (可选),
                    "amount": 金额 (可选)
                }
                
        Returns:
            Dict: 操作结果
                {
                    "success": bool,
                    "message": str,
                    "item": dict (更新后的项目)
                }
        """
        budget_data = self._load_budget(username)
        items = budget_data.get("items", [])
        
        # 查找项目
        item_index = None
        for i, item in enumerate(items):
            if item.get("id") == item_id:
                item_index = i
                break
        
        if item_index is None:
            return {
                "success": False,
                "message": f"未找到ID为 {item_id} 的项目",
                "item": None
            }
        
        current_item = items[item_index]
        
        # 验证并应用更新
        if "name" in updates:
            if not updates["name"].strip():
                return {
                    "success": False,
                    "message": "项目名称不能为空",
                    "item": None
                }
            current_item["name"] = updates["name"]
        
        if "scope" in updates:
            scope = updates["scope"]
            # 标准化 scope（支持英文）
            if scope in ["Permanent", "permanent", "永久"]:
                current_item["scope"] = "永久"
            elif "Year" in scope or "year" in scope:
                # 例如: "2025 Year 12 Month" -> "2025年12月"
                import re
                year_match = re.search(r'(\d{4})', scope)
                month_match = re.search(r'Month\s*(\d{1,2})|(\d{1,2})\s*Month', scope, re.IGNORECASE)
                if year_match:
                    year = year_match.group(1)
                    if month_match:
                        month = month_match.group(1) or month_match.group(2)
                        current_item["scope"] = f"{year}年{month}月"
                    else:
                        current_item["scope"] = f"{year}年"
            else:
                current_item["scope"] = scope
        
        if "time_type" in updates:
            time_type = updates["time_type"]
            valid_time_types = ["月度", "非月度", "Monthly", "monthly", "One-time", "one-time"]
            if time_type not in valid_time_types:
                return {
                    "success": False,
                    "message": "时间类别必须是'月度'/'Monthly'或'非月度'/'One-time'",
                    "item": None
                }
            # 标准化为中文
            if time_type in ["Monthly", "monthly"]:
                current_item["time_type"] = "月度"
            elif time_type in ["One-time", "one-time", "onetime"]:
                current_item["time_type"] = "非月度"
            else:
                current_item["time_type"] = time_type
        
        if "category" in updates:
            category = updates["category"]
            valid_categories = ["收入", "支出", "Income", "Expense"]
            if category not in valid_categories:
                return {
                    "success": False,
                    "message": "收支类别必须是'收入'/'Income'或'支出'/'Expense'",
                    "item": None
                }
            # 标准化为中文
            if category in ["Income", "income"]:
                current_item["category"] = "收入"
            elif category in ["Expense", "expense"]:
                current_item["category"] = "支出"
            else:
                current_item["category"] = category
        
        if "amount" in updates:
            try:
                amount = float(updates["amount"])
                if amount < 0:
                    return {
                        "success": False,
                        "message": "金额不能为负数",
                        "item": None
                    }
                current_item["amount"] = amount
            except (ValueError, TypeError):
                return {
                    "success": False,
                    "message": "金额必须是数字",
                    "item": None
                }
        
        # 更新修改时间
        current_item["updated_at"] = datetime.now().isoformat()
        
        # 保存数据
        budget_data["items"][item_index] = current_item
        self._save_budget(username, budget_data)
        
        return {
            "success": True,
            "message": "项目更新成功",
            "item": current_item
        }
    
    def delete_budget_item(self, username: str, item_id: str) -> Dict:
        """
        删除一个budget项目
        
        Args:
            username: 用户名
            item_id: 项目ID
            
        Returns:
            Dict: 操作结果
                {
                    "success": bool,
                    "message": str
                }
        """
        budget_data = self._load_budget(username)
        items = budget_data.get("items", [])
        
        # 查找并删除项目
        original_length = len(items)
        budget_data["items"] = [item for item in items if item.get("id") != item_id]
        
        if len(budget_data["items"]) == original_length:
            return {
                "success": False,
                "message": f"未找到ID为 {item_id} 的项目"
            }
        
        # 保存数据
        self._save_budget(username, budget_data)
        
        return {
            "success": True,
            "message": "项目删除成功"
        }
    
    def calculate_dashboard(self, username: str, year: int) -> Dict:
        """
        计算指定年份的dashboard统计数据
        
        计算逻辑：
        - 不同的年份相互独立
        - 单独的年份内：
            - 年度开支 = (月度开支 × 12) + 非月度开支
            - 年度收入 = (月度收入 × 12) + 非月度收入
            - 年度盈余 = 年度收入 - 年度开支
        
        Args:
            username: 用户名
            year: 年份
            
        Returns:
            Dict: 统计数据
                {
                    "year": 年份,
                    "total_income": 年度总收入,
                    "total_expense": 年度总支出,
                    "total_surplus": 年度总盈余,
                    "monthly_income": 月度收入总和,
                    "monthly_expense": 月度支出总和,
                    "non_monthly_income": 非月度收入总和,
                    "non_monthly_expense": 非月度支出总和
                }
        """
        budget_info = self.get_user_budget_info(username, year)
        items = budget_info["items"]
        
        # 初始化统计数据
        monthly_income = 0.0
        monthly_expense = 0.0
        non_monthly_income = 0.0
        non_monthly_expense = 0.0
        
        for item in items:
            amount = float(item.get("amount", 0))
            category = item.get("category")
            time_type = item.get("time_type")
            
            if time_type == "月度":
                if category == "收入":
                    monthly_income += amount
                elif category == "支出":
                    monthly_expense += amount
            elif time_type == "非月度":
                if category == "收入":
                    non_monthly_income += amount
                elif category == "支出":
                    non_monthly_expense += amount
        
        # 计算年度总计
        total_income = (monthly_income * 12) + non_monthly_income
        total_expense = (monthly_expense * 12) + non_monthly_expense
        total_surplus = total_income - total_expense
        
        return {
            "year": year,
            "total_income": total_income,
            "total_expense": total_expense,
            "total_surplus": total_surplus,
            "monthly_income": monthly_income,
            "monthly_expense": monthly_expense,
            "non_monthly_income": non_monthly_income,
            "non_monthly_expense": non_monthly_expense
        }
    
    def get_items_by_month(self, username: str, year: int, months: Optional[List[int]] = None) -> Dict:
        """
        获取指定年份和月份的项目
        
        Args:
            username: 用户名
            year: 年份
            months: 月份列表（1-12），None表示所有月份
            
        Returns:
            Dict: 过滤后的项目
                {
                    "income_items": [...],  # 收入项目
                    "expense_items": [...]  # 支出项目
                }
        """
        budget_info = self.get_user_budget_info(username, year)
        items = budget_info["items"]
        
        income_items = []
        expense_items = []
        
        for item in items:
            category = item.get("category")
            time_type = item.get("time_type")
            scope = item.get("scope", "")
            
            # 判断是否包含该项目
            include_item = False
            
            if time_type == "月度":
                # 月度项目总是显示
                include_item = True
            elif time_type == "非月度":
                # 非月度项目需要检查月份
                if months is None:
                    # 显示所有月份
                    include_item = True
                else:
                    # 检查项目的月份是否在选中的月份中
                    if "月" in scope:
                        try:
                            # 从 "2025年12月" 提取月份
                            month_part = scope.split("年")[1].replace("月", "")
                            item_month = int(month_part)
                            if item_month in months:
                                include_item = True
                        except (IndexError, ValueError):
                            # 如果无法解析月份，显示该项目
                            include_item = True
                    else:
                        # 没有具体月份的非月度项目（如"2025年"），显示
                        include_item = True
            
            if include_item:
                if category == "收入":
                    income_items.append(item)
                elif category == "支出":
                    expense_items.append(item)
        
        return {
            "income_items": income_items,
            "expense_items": expense_items
        }


# 创建全局实例
budget_planner = BudgetPlanner()


# 导出的公共函数
def get_user_budget_info(username: str, year: Optional[int] = None) -> Dict:
    """获取用户的budget内容和信息"""
    return budget_planner.get_user_budget_info(username, year)


def add_budget_item(username: str, item: Dict) -> Dict:
    """添加一个budget项目"""
    return budget_planner.add_budget_item(username, item)


def update_budget_item(username: str, item_id: str, updates: Dict) -> Dict:
    """更新一个budget项目"""
    return budget_planner.update_budget_item(username, item_id, updates)


def delete_budget_item(username: str, item_id: str) -> Dict:
    """删除一个budget项目"""
    return budget_planner.delete_budget_item(username, item_id)


def calculate_dashboard(username: str, year: int) -> Dict:
    """计算指定年份的dashboard统计数据"""
    return budget_planner.calculate_dashboard(username, year)


def get_items_by_month(username: str, year: int, months: Optional[List[int]] = None) -> Dict:
    """获取指定年份和月份的项目"""
    return budget_planner.get_items_by_month(username, year, months)
