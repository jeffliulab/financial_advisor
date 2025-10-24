"""
Budget Planner Test Panel - Budget Planning Test Interface

Test panel for budget planner database, API and functionality.
Features:
- Add/delete budget items
- View income/expense items
- Test dashboard calculations
- Switch between users and years

Purpose: Test interfaces and functions for future agent system integration.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "brain" / "tools"))

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
from datetime import datetime
from budget_planner import (
    get_user_budget_info,
    add_budget_item,
    update_budget_item,
    delete_budget_item,
    calculate_dashboard,
    get_items_by_month
)


class BudgetTestPanel:
    """Budget Planning Test Panel"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Budget Planner Test Panel")
        
        # Set window size and make it resizable
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = min(1400, int(screen_width * 0.8))
        window_height = min(900, int(screen_height * 0.85))
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Configure high DPI scaling
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
        
        # Current user and year
        self.current_user = "admin"
        self.current_year = datetime.now().year
        
        # Month filter
        self.selected_months = list(range(1, 13))
        
        # Style configuration
        self.setup_styles()
        
        # Create UI
        self.create_ui()
        
        # Load initial data
        self.refresh_data()
    
    def setup_styles(self):
        """Setup custom styles for better appearance"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=('Segoe UI', 10))
        style.configure('TLabelframe', background='#f0f0f0', font=('Segoe UI', 10, 'bold'))
        style.configure('TLabelframe.Label', background='#f0f0f0', font=('Segoe UI', 10, 'bold'))
        style.configure('TButton', font=('Segoe UI', 9))
        style.configure('Header.TLabel', font=('Segoe UI', 14, 'bold'))
        style.configure('Dashboard.TLabel', font=('Segoe UI', 12, 'bold'), foreground='#2563eb')
        
    def create_ui(self):
        """Create user interface"""
        
        # ==== Top Control Panel ====
        control_frame = ttk.Frame(self.root, padding="15")
        control_frame.pack(fill=tk.X)
        
        # User section
        user_frame = ttk.LabelFrame(control_frame, text=" User Settings ", padding="10")
        user_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(user_frame, text="Username:").grid(row=0, column=0, padx=(0, 5), sticky=tk.W)
        self.user_entry = ttk.Entry(user_frame, width=15, font=('Segoe UI', 10))
        self.user_entry.insert(0, self.current_user)
        self.user_entry.grid(row=0, column=1, padx=5)
        
        ttk.Button(user_frame, text="Switch User", 
                  command=self.switch_user, width=12).grid(row=0, column=2, padx=5)
        
        # Year section
        year_frame = ttk.LabelFrame(control_frame, text=" Year Settings ", padding="10")
        year_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(year_frame, text="Year:").grid(row=0, column=0, padx=(0, 5), sticky=tk.W)
        self.year_var = tk.StringVar(value=str(self.current_year))
        year_spinbox = ttk.Spinbox(
            year_frame,
            from_=2020,
            to=2035,
            textvariable=self.year_var,
            width=10,
            font=('Segoe UI', 10)
        )
        year_spinbox.grid(row=0, column=1, padx=5)
        year_spinbox.bind('<Return>', lambda e: self.on_year_change())
        year_spinbox.bind('<FocusOut>', lambda e: self.on_year_change())
        
        ttk.Button(year_frame, text="Apply Year", 
                  command=self.on_year_change, width=12).grid(row=0, column=2, padx=5)
        
        # Refresh button
        ttk.Button(control_frame, text="🔄 Refresh All", 
                  command=self.refresh_data, width=15).pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_label = ttk.Label(control_frame, text=f"User: {self.current_user} | Year: {self.current_year}",
                                     font=('Segoe UI', 9, 'italic'), foreground='#6b7280')
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # ==== Dashboard Panel ====
        dashboard_frame = ttk.LabelFrame(self.root, text=" Dashboard Statistics ", padding="15")
        dashboard_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        self.dashboard_label = ttk.Label(
            dashboard_frame,
            text="Annual Income: $0 | Annual Expense: $0 | Annual Surplus: $0",
            style='Dashboard.TLabel'
        )
        self.dashboard_label.pack()
        
        # ==== Main Content Area ====
        content_frame = ttk.Frame(self.root)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
        
        # Left panel: Add items
        left_panel = ttk.LabelFrame(content_frame, text=" Add Budget Item ", padding="15")
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.create_add_form(left_panel)
        
        # Right panel: View items
        right_panel = ttk.LabelFrame(content_frame, text=" Budget Items ", padding="15")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.create_items_view(right_panel)
        
        # ==== Bottom Log Panel ====
        log_frame = ttk.LabelFrame(self.root, text=" Operation Log ", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=False, padx=15, pady=(0, 15))
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=6, 
            wrap=tk.WORD,
            font=('Consolas', 9),
            bg='#1e1e1e',
            fg='#d4d4d4',
            insertbackground='white'
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
    def create_add_form(self, parent):
        """Create the add item form"""
        form_frame = ttk.Frame(parent)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Item name
        ttk.Label(form_frame, text="Item Name:").grid(row=0, column=0, sticky=tk.W, pady=8, padx=(0, 10))
        self.name_entry = ttk.Entry(form_frame, width=30, font=('Segoe UI', 10))
        self.name_entry.grid(row=0, column=1, columnspan=2, pady=8, sticky=tk.W+tk.E)
        
        # Scope
        ttk.Label(form_frame, text="Scope:").grid(row=1, column=0, sticky=tk.W, pady=8, padx=(0, 10))
        scope_frame = ttk.Frame(form_frame)
        scope_frame.grid(row=1, column=1, columnspan=2, pady=8, sticky=tk.W)
        
        self.scope_var = tk.StringVar(value="永久")
        ttk.Radiobutton(scope_frame, text="Permanent", variable=self.scope_var, 
                       value="永久").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(scope_frame, text="Specific Date", variable=self.scope_var, 
                       value="指定").pack(side=tk.LEFT)
        
        # Year and month for specific scope
        date_frame = ttk.Frame(form_frame)
        date_frame.grid(row=2, column=1, columnspan=2, pady=5, sticky=tk.W)
        
        ttk.Label(date_frame, text="Year:").pack(side=tk.LEFT, padx=(0, 5))
        self.scope_year_var = tk.StringVar(value=str(self.current_year))
        ttk.Entry(date_frame, textvariable=self.scope_year_var, width=8).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(date_frame, text="Month (optional):").pack(side=tk.LEFT, padx=(0, 5))
        self.scope_month_var = tk.StringVar(value="")
        ttk.Entry(date_frame, textvariable=self.scope_month_var, width=5).pack(side=tk.LEFT)
        
        # Time type
        ttk.Label(form_frame, text="Time Type:").grid(row=3, column=0, sticky=tk.W, pady=8, padx=(0, 10))
        time_frame = ttk.Frame(form_frame)
        time_frame.grid(row=3, column=1, columnspan=2, pady=8, sticky=tk.W)
        
        self.time_type_var = tk.StringVar(value="月度")
        ttk.Radiobutton(time_frame, text="Monthly", variable=self.time_type_var, 
                       value="月度").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(time_frame, text="One-time", variable=self.time_type_var, 
                       value="非月度").pack(side=tk.LEFT)
        
        # Category
        ttk.Label(form_frame, text="Category:").grid(row=4, column=0, sticky=tk.W, pady=8, padx=(0, 10))
        category_frame = ttk.Frame(form_frame)
        category_frame.grid(row=4, column=1, columnspan=2, pady=8, sticky=tk.W)
        
        self.category_var = tk.StringVar(value="收入")
        ttk.Radiobutton(category_frame, text="Income", variable=self.category_var, 
                       value="收入").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(category_frame, text="Expense", variable=self.category_var, 
                       value="支出").pack(side=tk.LEFT)
        
        # Amount
        ttk.Label(form_frame, text="Amount ($):").grid(row=5, column=0, sticky=tk.W, pady=8, padx=(0, 10))
        self.amount_entry = ttk.Entry(form_frame, width=20, font=('Segoe UI', 10))
        self.amount_entry.grid(row=5, column=1, pady=8, sticky=tk.W)
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=20)
        
        ttk.Button(button_frame, text="✅ Add Item", 
                  command=self.add_item, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔄 Clear Form", 
                  command=self.clear_form, width=15).pack(side=tk.LEFT, padx=5)
        
        # Quick add examples
        ttk.Separator(form_frame, orient='horizontal').grid(row=7, column=0, columnspan=3, 
                                                            sticky=tk.W+tk.E, pady=10)
        ttk.Label(form_frame, text="Quick Examples:", 
                 font=('Segoe UI', 9, 'bold')).grid(row=8, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        example_frame = ttk.Frame(form_frame)
        example_frame.grid(row=9, column=0, columnspan=3, pady=5)
        
        ttk.Button(example_frame, text="💰 Salary", 
                  command=lambda: self.quick_add("工资", "永久", "月度", "收入", "5000"),
                  width=12).pack(side=tk.LEFT, padx=3)
        ttk.Button(example_frame, text="🏠 Rent", 
                  command=lambda: self.quick_add("房租", "永久", "月度", "支出", "2000"),
                  width=12).pack(side=tk.LEFT, padx=3)
        ttk.Button(example_frame, text="✈️ Travel", 
                  command=lambda: self.quick_add("旅行", f"{self.current_year}年12月", "非月度", "支出", "5000"),
                  width=12).pack(side=tk.LEFT, padx=3)
        
        # Configure grid weights
        form_frame.columnconfigure(1, weight=1)
        
    def create_items_view(self, parent):
        """Create the items view panel"""
        # Month filter
        filter_frame = ttk.Frame(parent)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(filter_frame, text="Month Filter:", 
                 font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(filter_frame, text="All", command=self.select_all_months,
                  width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="None", command=self.deselect_all_months,
                  width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="Apply", command=self.refresh_items,
                  width=8).pack(side=tk.LEFT, padx=2)
        
        # Month checkboxes
        month_frame = ttk.Frame(parent)
        month_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.month_vars = {}
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        for i, name in enumerate(month_names):
            var = tk.BooleanVar(value=True)
            self.month_vars[i + 1] = var
            ttk.Checkbutton(month_frame, text=name, variable=var,
                          command=self.on_month_change).pack(side=tk.LEFT, padx=2)
        
        # Notebook for income/expense tabs
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Income tab
        income_frame = ttk.Frame(self.notebook)
        self.notebook.add(income_frame, text="📈 Income Items")
        
        self.income_tree = self.create_tree(income_frame)
        
        # Expense tab
        expense_frame = ttk.Frame(self.notebook)
        self.notebook.add(expense_frame, text="💳 Expense Items")
        
        self.expense_tree = self.create_tree(expense_frame)
        
        # Delete button
        delete_frame = ttk.Frame(parent)
        delete_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(delete_frame, text="✏️ Edit Selected Item",
                  command=self.edit_selected, width=25).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(delete_frame, text="🗑️ Delete Selected Item",
                  command=self.delete_selected, width=25).pack(side=tk.LEFT)
        
    def create_tree(self, parent):
        """Create a treeview widget"""
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview
        tree = ttk.Treeview(
            tree_frame,
            columns=("name", "scope", "time_type", "amount"),
            show="headings",
            yscrollcommand=scrollbar.set,
            height=15
        )
        
        tree.heading("name", text="Item Name")
        tree.heading("scope", text="Scope")
        tree.heading("time_type", text="Type")
        tree.heading("amount", text="Amount ($)")
        
        tree.column("name", width=150)
        tree.column("scope", width=120)
        tree.column("time_type", width=80)
        tree.column("amount", width=100)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=tree.yview)
        
        return tree
    
    def log(self, message: str, level: str = "INFO"):
        """Add a log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        color_codes = {
            "INFO": "#4ade80",
            "SUCCESS": "#22c55e",
            "ERROR": "#ef4444",
            "WARNING": "#f59e0b"
        }
        
        color = color_codes.get(level, "#d4d4d4")
        
        self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.log_text.insert(tk.END, f"[{level}] ", level)
        self.log_text.insert(tk.END, f"{message}\n")
        
        self.log_text.tag_config("timestamp", foreground="#6b7280")
        self.log_text.tag_config(level, foreground=color, font=('Consolas', 9, 'bold'))
        self.log_text.see(tk.END)
        
    def switch_user(self):
        """Switch user"""
        new_user = self.user_entry.get().strip()
        if not new_user:
            messagebox.showwarning("Warning", "Username cannot be empty")
            return
        
        self.current_user = new_user
        self.status_label.config(text=f"User: {self.current_user} | Year: {self.current_year}")
        self.log(f"Switched to user: {self.current_user}", "SUCCESS")
        self.refresh_data()
        
    def on_year_change(self):
        """Handle year change"""
        try:
            new_year = int(self.year_var.get())
            if new_year < 2020 or new_year > 2035:
                messagebox.showwarning("Warning", "Year must be between 2020 and 2035")
                self.year_var.set(str(self.current_year))
                return
            
            self.current_year = new_year
            self.status_label.config(text=f"User: {self.current_user} | Year: {self.current_year}")
            self.log(f"Changed to year: {self.current_year}", "SUCCESS")
            self.refresh_data()
        except ValueError:
            messagebox.showerror("Error", "Invalid year format")
            self.year_var.set(str(self.current_year))
        
    def refresh_data(self):
        """Refresh all data"""
        self.log(f"Refreshing data for user={self.current_user}, year={self.current_year}", "INFO")
        self.refresh_dashboard()
        self.refresh_items()
        
    def refresh_dashboard(self):
        """Refresh dashboard statistics"""
        try:
            dashboard_data = calculate_dashboard(self.current_user, self.current_year)
            
            text = (
                f"Annual Income: ${dashboard_data['total_income']:.2f} | "
                f"Annual Expense: ${dashboard_data['total_expense']:.2f} | "
                f"Annual Surplus: ${dashboard_data['total_surplus']:.2f}"
            )
            
            self.dashboard_label.config(text=text)
            self.log("Dashboard refreshed successfully", "SUCCESS")
            
        except Exception as e:
            self.log(f"Failed to refresh dashboard: {str(e)}", "ERROR")
            
    def refresh_items(self):
        """Refresh items list"""
        try:
            # Get selected months
            months = [month for month, var in self.month_vars.items() if var.get()]
            months = months if months else None
            
            # Get items
            items_data = get_items_by_month(self.current_user, self.current_year, months)
            
            # Clear trees
            for item in self.income_tree.get_children():
                self.income_tree.delete(item)
            for item in self.expense_tree.get_children():
                self.expense_tree.delete(item)
            
            # Fill income items
            for item in items_data["income_items"]:
                self.income_tree.insert(
                    "",
                    tk.END,
                    values=(
                        item["name"],
                        item["scope"],
                        "Monthly" if item["time_type"] == "月度" else "One-time",
                        f"{float(item['amount']):.2f}"
                    ),
                    tags=(item["id"],)
                )
            
            # Fill expense items
            for item in items_data["expense_items"]:
                self.expense_tree.insert(
                    "",
                    tk.END,
                    values=(
                        item["name"],
                        item["scope"],
                        "Monthly" if item["time_type"] == "月度" else "One-time",
                        f"{float(item['amount']):.2f}"
                    ),
                    tags=(item["id"],)
                )
            
            self.log(f"Items refreshed: {len(items_data['income_items'])} income, "
                    f"{len(items_data['expense_items'])} expense", "SUCCESS")
            
        except Exception as e:
            self.log(f"Failed to refresh items: {str(e)}", "ERROR")
            
    def add_item(self):
        """Add a new item or update existing item"""
        try:
            # Check if in edit mode
            is_edit_mode = hasattr(self, 'editing_item_id')
            
            # Get input
            name = self.name_entry.get().strip()
            if not name:
                messagebox.showwarning("Warning", "Item name cannot be empty")
                return
            
            # Build scope
            if self.scope_var.get() == "永久":
                scope = "永久"
            else:
                year = self.scope_year_var.get()
                month = self.scope_month_var.get().strip()
                scope = f"{year}年{month}月" if month else f"{year}年"
            
            time_type = self.time_type_var.get()
            category = self.category_var.get()
            
            amount = self.amount_entry.get().strip()
            if not amount:
                messagebox.showwarning("Warning", "Amount cannot be empty")
                return
            
            try:
                amount = float(amount)
            except ValueError:
                messagebox.showwarning("Warning", "Amount must be a number")
                return
            
            if is_edit_mode:
                # Update existing item
                updates = {
                    "name": name,
                    "scope": scope,
                    "time_type": time_type,
                    "category": category,
                    "amount": amount
                }
                
                result = update_budget_item(self.current_user, self.editing_item_id, updates)
                
                if result["success"]:
                    self.log(f"Updated item: {name} - ${amount}", "SUCCESS")
                    messagebox.showinfo("Success", result["message"])
                    
                    # Clear form and exit edit mode
                    self.clear_form()
                    
                    # Refresh data
                    self.refresh_data()
                else:
                    self.log(f"Failed to update item: {result['message']}", "ERROR")
                    messagebox.showerror("Error", result["message"])
            else:
                # Add new item
                item = {
                    "name": name,
                    "scope": scope,
                    "time_type": time_type,
                    "category": category,
                    "amount": amount
                }
                
                # Call API
                result = add_budget_item(self.current_user, item)
                
                if result["success"]:
                    self.log(f"Added item: {name} - ${amount}", "SUCCESS")
                    messagebox.showinfo("Success", result["message"])
                    
                    # Clear form
                    self.clear_form()
                    
                    # Refresh data
                    self.refresh_data()
                else:
                    self.log(f"Failed to add item: {result['message']}", "ERROR")
                    messagebox.showerror("Error", result["message"])
                
        except Exception as e:
            self.log(f"Exception while adding/updating item: {str(e)}", "ERROR")
            messagebox.showerror("Exception", str(e))
            
    def delete_selected(self):
        """Delete selected item"""
        try:
            # Determine which tab is active
            current_tab = self.notebook.index(self.notebook.select())
            tree = self.income_tree if current_tab == 0 else self.expense_tree
            type_name = "income" if current_tab == 0 else "expense"
            
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Warning", f"Please select a {type_name} item to delete")
                return
            
            # Get item ID
            item_id = tree.item(selected[0])["tags"][0]
            
            # Confirm
            if not messagebox.askyesno("Confirm", f"Delete this {type_name} item?"):
                return
            
            # Call API
            result = delete_budget_item(self.current_user, item_id)
            
            if result["success"]:
                self.log(f"Deleted item: ID={item_id}", "SUCCESS")
                messagebox.showinfo("Success", result["message"])
                
                # Refresh data
                self.refresh_data()
            else:
                self.log(f"Failed to delete item: {result['message']}", "ERROR")
                messagebox.showerror("Error", result["message"])
                
        except Exception as e:
            self.log(f"Exception while deleting item: {str(e)}", "ERROR")
            messagebox.showerror("Exception", str(e))
    
    def edit_selected(self):
        """Edit selected item"""
        try:
            # Determine which tab is active
            current_tab = self.notebook.index(self.notebook.select())
            tree = self.income_tree if current_tab == 0 else self.expense_tree
            type_name = "income" if current_tab == 0 else "expense"
            
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Warning", f"Please select a {type_name} item to edit")
                return
            
            # Get item ID and current values
            item_id = tree.item(selected[0])["tags"][0]
            values = tree.item(selected[0])["values"]
            
            # Get full item data from budget
            budget_info = get_user_budget_info(self.current_user, self.current_year)
            item_data = None
            for item in budget_info["items"]:
                if item.get("id") == item_id:
                    item_data = item
                    break
            
            if not item_data:
                messagebox.showerror("Error", "Item not found in budget data")
                return
            
            # Fill form with current data
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, item_data["name"])
            
            scope = item_data["scope"]
            if scope == "永久":
                self.scope_var.set("永久")
                self.scope_month_var.set("")
            else:
                self.scope_var.set("指定")
                if "年" in scope:
                    parts = scope.split("年")
                    self.scope_year_var.set(parts[0])
                    if len(parts) > 1 and parts[1]:
                        self.scope_month_var.set(parts[1].replace("月", ""))
                    else:
                        self.scope_month_var.set("")
            
            self.time_type_var.set(item_data["time_type"])
            self.category_var.set(item_data["category"])
            
            self.amount_entry.delete(0, tk.END)
            self.amount_entry.insert(0, str(item_data["amount"]))
            
            # Store current editing item ID
            self.editing_item_id = item_id
            
            # Change button text to indicate edit mode
            for widget in self.root.winfo_children():
                self._find_and_update_button(widget)
            
            self.log(f"Editing item: {item_data['name']} (ID: {item_id})", "INFO")
            messagebox.showinfo("Edit Mode", 
                              f"Now editing: {item_data['name']}\n\n"
                              "Modify the form and click 'Update Item' to save changes.")
            
        except Exception as e:
            self.log(f"Exception while loading item for edit: {str(e)}", "ERROR")
            messagebox.showerror("Exception", str(e))
    
    def _find_and_update_button(self, widget):
        """Recursively find and update the add button"""
        if isinstance(widget, ttk.Button):
            if "Add Item" in str(widget.cget("text")):
                widget.config(text="✅ Update Item")
        for child in widget.winfo_children():
            self._find_and_update_button(child)
            
    def clear_form(self):
        """Clear the add form"""
        self.name_entry.delete(0, tk.END)
        self.amount_entry.delete(0, tk.END)
        self.scope_month_var.set("")
        self.scope_var.set("永久")
        self.time_type_var.set("月度")
        self.category_var.set("收入")
        
        # Reset edit mode
        if hasattr(self, 'editing_item_id'):
            delattr(self, 'editing_item_id')
            # Restore button text
            for widget in self.root.winfo_children():
                self._find_and_restore_button(widget)
    
    def _find_and_restore_button(self, widget):
        """Recursively find and restore the add button"""
        if isinstance(widget, ttk.Button):
            if "Update Item" in str(widget.cget("text")):
                widget.config(text="✅ Add Item")
        for child in widget.winfo_children():
            self._find_and_restore_button(child)
        
    def quick_add(self, name, scope, time_type, category, amount):
        """Quick add example"""
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, name)
        
        if scope == "永久":
            self.scope_var.set("永久")
        else:
            self.scope_var.set("指定")
            if "年" in scope:
                parts = scope.split("年")
                self.scope_year_var.set(parts[0])
                if len(parts) > 1 and parts[1]:
                    self.scope_month_var.set(parts[1].replace("月", ""))
        
        self.time_type_var.set(time_type)
        self.category_var.set(category)
        
        self.amount_entry.delete(0, tk.END)
        self.amount_entry.insert(0, amount)
        
        self.log(f"Quick example loaded: {name}", "INFO")
        
    def on_month_change(self):
        """Handle month filter change"""
        selected = sum(1 for var in self.month_vars.values() if var.get())
        self.log(f"Month filter changed: {selected} months selected", "INFO")
        
    def select_all_months(self):
        """Select all months"""
        for var in self.month_vars.values():
            var.set(True)
        self.log("All months selected", "INFO")
        
    def deselect_all_months(self):
        """Deselect all months"""
        for var in self.month_vars.values():
            var.set(False)
        self.log("All months deselected", "INFO")


def main():
    """Main function"""
    root = tk.Tk()
    app = BudgetTestPanel(root)
    
    # Center window on screen
    root.update_idletasks()
    
    # Start application
    root.mainloop()


if __name__ == "__main__":
    main()
