import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import requests
from datetime import datetime
from PIL import Image, ImageTk
import io
import os

# -----------------------
# API endpoints
# -----------------------
API_BASE = "http://127.0.0.1:8000/api/"
API_PRODUCTS = f"{API_BASE}products/"
API_PURCHASE = f"{API_BASE}purchase/"
API_TRANSACTIONS = f"{API_BASE}purchases/"

VALID_DENOMINATIONS = [5, 10, 20, 25, 50, 100, 200]

# ---------- COLORS ----------
PRIMARY_COLOR = "#2c3e50"
SECONDARY_COLOR = "#3498db"
ACCENT_COLOR = "#e74c3c"
SUCCESS_COLOR = "#27ae60"
WARNING_COLOR = "#f39c12"
INFO_COLOR = "#17a2b8"
BG_COLOR = "#ecf0f1"
HEADER_BG = "#34495e"
HEADER_FG = "#ffffff"
CARD_BG = "#ffffff"
ROW_ODD = "#f8f9fa"
ROW_EVEN = "#e9ecef"
BTN_PRIMARY = "#2980b9"
BTN_SUCCESS = "#27ae60"
BTN_DANGER = "#e74c3c"
BTN_WARNING = "#f39c12"

class VendingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Polytechnic Vending Machine - Management System")
        self.root.configure(bg=BG_COLOR)
        self.products = []
        self.cart = {}
        self.total_cost = 0
        self.student_name = ""
        self.admin_tree = None
        self.product_tree = None
        self.product_images = {}

        # Configure styles
        self.setup_styles()
        
        self.main_frame = tk.Frame(root, bg=BG_COLOR)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.show_role_selection()

    def setup_styles(self):
        style = ttk.Style()
        style.configure("Custom.TButton", padding=10, relief="flat", background=BTN_PRIMARY)
        style.configure("Success.TButton", background=BTN_SUCCESS)
        style.configure("Danger.TButton", background=BTN_DANGER)
        style.configure("Warning.TButton", background=BTN_WARNING)

    # ---------- Utilities ----------
    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def create_styled_button(self, parent, text, command, bg=BTN_PRIMARY, width=20, height=2):
        btn = tk.Button(parent, text=text, width=width, height=height, 
                       bg=bg, fg="white", font=("Arial", 10, "bold"),
                       relief="flat", cursor="hand2", command=command,
                       bd=0, highlightthickness=0)
        # Hover effects
        def on_enter(e):
            btn['bg'] = self.adjust_color(bg, 20)  # Lighten
        def on_leave(e):
            btn['bg'] = bg
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def adjust_color(self, color, amount):
        """Lighten or darken a color"""
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        new_rgb = tuple(max(0, min(255, c + amount)) for c in rgb)
        return f"#{new_rgb[0]:02x}{new_rgb[1]:02x}{new_rgb[2]:02x}"

    def create_card(self, parent, title, content):
        card = tk.Frame(parent, bg=CARD_BG, relief="raised", bd=1)
        tk.Label(card, text=title, bg=CARD_BG, fg=PRIMARY_COLOR, 
                font=("Arial", 12, "bold")).pack(pady=10)
        content_frame = tk.Frame(card, bg=CARD_BG)
        content_frame.pack(pady=10)
        return card, content_frame

    # ---------- Role Selection ----------
    def show_role_selection(self):
        self.clear_frame()
        
        # Header
        header_frame = tk.Frame(self.main_frame, bg=HEADER_BG)
        header_frame.pack(fill="x", pady=(0, 30))
        
        tk.Label(header_frame, text="🎯 Vending Machine System", 
                font=("Arial", 24, "bold"), bg=HEADER_BG, fg=HEADER_FG).pack(pady=20)
        
        tk.Label(header_frame, text="Polytechnic Management Platform", 
                font=("Arial", 14), bg=HEADER_BG, fg=HEADER_FG).pack(pady=5)

        # Cards container
        cards_frame = tk.Frame(self.main_frame, bg=BG_COLOR)
        cards_frame.pack(fill="both", expand=True)

        # Student Card
        student_card, student_content = self.create_card(cards_frame, "Student Portal", "Make purchases and browse products")
        student_card.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        tk.Label(student_content, text="Quick Purchase Access", bg=CARD_BG, 
                font=("Arial", 10), fg=SECONDARY_COLOR).pack(pady=10)
        self.create_styled_button(student_content, "Enter as Student", 
                                self.student_login, bg=SUCCESS_COLOR).pack(pady=15)

        # Admin Card
        admin_card, admin_content = self.create_card(cards_frame, "Admin Portal", "Manage products and view analytics")
        admin_card.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        tk.Label(admin_content, text="System Management", bg=CARD_BG,
                font=("Arial", 10), fg=WARNING_COLOR).pack(pady=10)
        self.create_styled_button(admin_content, "Enter as Admin", 
                                self.admin_login, bg=WARNING_COLOR).pack(pady=15)

    # ---------- Student ----------
    def student_login(self):
        self.clear_frame()
        self.student_name = simpledialog.askstring("Student Login", "Enter your name:", 
                                                  parent=self.root)
        if not self.student_name:
            messagebox.showerror("Error", "Name is required")
            self.show_role_selection()
            return
        if not self.fetch_products(show_errors=True):
            self.show_role_selection()
            return
        self.show_student_interface()

    def fetch_products(self, show_errors=False):
        try:
            response = requests.get(API_PRODUCTS, timeout=10)
            response.raise_for_status()
            products = response.json()
            self.products = []
            for p in products:
                product_data = {
                    "id": p.get("id"),
                    "name": p.get("product_name", p.get("name", "Unknown")),
                    "price": float(p.get("cost", p.get("price", 0))),
                    "quantity": int(p.get("available_quantity", p.get("quantity", 0))),
                    "category": p.get("category", ""),
                    "is_available": p.get("is_available", True),
                    "image_url": p.get("image", None)
                }
                self.products.append(product_data)
                
                # Load product image if available
                if product_data["image_url"]:
                    self.load_product_image(product_data["id"], product_data["image_url"])
                    
            return True
        except requests.exceptions.RequestException as e:
            if show_errors:
                messagebox.showerror("Connection Error", 
                                   f"Cannot connect to Django server.\nError: {str(e)}")
            return False

    def load_product_image(self, product_id, image_url):
        try:
            if image_url and image_url.startswith('http'):
                response = requests.get(image_url, timeout=10)
                if response.status_code == 200:
                    image_data = response.content
                    image = Image.open(io.BytesIO(image_data))
                    image = image.resize((80, 80), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(image)
                    self.product_images[product_id] = photo
            else:
                # Create a default image placeholder
                self.create_default_image(product_id)
        except Exception as e:
            print(f"Error loading image for product {product_id}: {e}")
            self.create_default_image(product_id)

    def create_default_image(self, product_id):
        """Create a default placeholder image"""
        try:
            # Create a simple colored rectangle as placeholder
            image = Image.new('RGB', (80, 80), color='#3498db')
            photo = ImageTk.PhotoImage(image)
            self.product_images[product_id] = photo
        except:
            pass

    def show_student_interface(self):
        self.clear_frame()
        
        # Header
        header_frame = tk.Frame(self.main_frame, bg=HEADER_BG)
        header_frame.pack(fill="x", pady=(0, 20))
        
        tk.Label(header_frame, text=f"👤 Student: {self.student_name}", 
                font=("Arial", 16, "bold"), bg=HEADER_BG, fg=HEADER_FG).pack(side="left", padx=15, pady=10)
        
        button_frame = tk.Frame(header_frame, bg=HEADER_BG)
        button_frame.pack(side="right", padx=10, pady=5)
        
        self.create_styled_button(button_frame, "🔄 Refresh", self.refresh_student, 
                                 bg=INFO_COLOR, width=12).pack(side="left", padx=5)
        self.create_styled_button(button_frame, "⬅ Back", self.show_role_selection, 
                                 bg=ACCENT_COLOR, width=10).pack(side="left", padx=5)

        # Main content frame
        content_frame = tk.Frame(self.main_frame, bg=BG_COLOR)
        content_frame.pack(fill="both", expand=True)

        # Products frame (left)
        products_frame = tk.LabelFrame(content_frame, text="🛍️ Available Products", 
                                      font=("Arial", 12, "bold"), bg=BG_COLOR, fg=PRIMARY_COLOR)
        products_frame.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=10)

        # Create products grid
        self.create_products_grid(products_frame)

        # Cart frame (right)
        cart_frame = tk.LabelFrame(content_frame, text="🛒 Your Cart", 
                                  font=("Arial", 12, "bold"), bg=BG_COLOR, fg=PRIMARY_COLOR)
        cart_frame.pack(side="right", fill="y", padx=(10, 0), pady=10, ipadx=10)

        self.create_cart_section(cart_frame)

    def create_products_grid(self, parent):
        # Canvas and scrollbar for products
        canvas = tk.Canvas(parent, bg=BG_COLOR, highlightthickness=0)
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=BG_COLOR)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")

        self.cart = {}
        self.total_cost = 0

        # Create product cards in a grid
        row, col = 0, 0
        max_cols = 3  # 3 products per row
        
        for i, prod in enumerate(self.products):
            if not prod['is_available'] or prod['quantity'] <= 0:
                continue
                
            product_card = self.create_product_card(scrollable_frame, prod, i)
            product_card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        # Configure grid weights for responsive layout
        for i in range(max_cols):
            scrollable_frame.grid_columnconfigure(i, weight=1)

    def create_product_card(self, parent, product, index):
        bg_color = ROW_ODD if index % 2 == 0 else ROW_EVEN
        card = tk.Frame(parent, bg=bg_color, relief="raised", bd=1, width=200, height=180)
        
        # Product image
        image_frame = tk.Frame(card, bg=bg_color)
        image_frame.pack(pady=5)
        
        if product['id'] in self.product_images:
            img_label = tk.Label(image_frame, image=self.product_images[product['id']], bg=bg_color, cursor="hand2")
        else:
            img_label = tk.Label(image_frame, text="🖼️", font=("Arial", 20), bg=bg_color, cursor="hand2")
        img_label.pack()
        
        # Product info
        info_frame = tk.Frame(card, bg=bg_color)
        info_frame.pack(fill="x", pady=5)
        
        # Product name (clickable)
        name_label = tk.Label(info_frame, text=product['name'], bg=bg_color, 
                font=("Arial", 10, "bold"), wraplength=180, cursor="hand2")
        name_label.pack()
        
        tk.Label(info_frame, text=f"Rs {product['price']:.2f}", bg=bg_color,
                font=("Arial", 9, "bold"), fg=SUCCESS_COLOR).pack()
        
        stock_text = f"Stock: {product['quantity']}"
        stock_color = ACCENT_COLOR if product['quantity'] == 0 else PRIMARY_COLOR
        tk.Label(info_frame, text=stock_text, bg=bg_color, font=("Arial", 8), fg=stock_color).pack()
        
        # Quantity controls
        control_frame = tk.Frame(card, bg=bg_color)
        control_frame.pack(pady=5)
        
        qty_var = tk.IntVar(value=0)
        
        def decrease_qty():
            if qty_var.get() > 0:
                qty_var.set(qty_var.get() - 1)
        
        def increase_qty():
            if qty_var.get() < product['quantity']:
                qty_var.set(qty_var.get() + 1)
        
        tk.Button(control_frame, text="➖", command=decrease_qty, 
                 bg=ACCENT_COLOR, fg="white", font=("Arial", 8), width=3).pack(side="left")
        
        qty_label = tk.Label(control_frame, textvariable=qty_var, bg="white", 
                           width=3, relief="sunken", font=("Arial", 9))
        qty_label.pack(side="left", padx=2)
        
        tk.Button(control_frame, text="➕", command=increase_qty,
                 bg=SUCCESS_COLOR, fg="white", font=("Arial", 8), width=3).pack(side="left")
        
        # Add click functionality to product name and image
        def on_product_click(event):
            if product['quantity'] > 0:
                current_qty = qty_var.get()
                qty_var.set(current_qty + 1)
        
        img_label.bind("<Button-1>", on_product_click)
        name_label.bind("<Button-1>", on_product_click)
        qty_label.bind("<Button-1>", on_product_click)
        
        self.cart[product['id']] = qty_var
        qty_var.trace_add("write", lambda *args: self.update_total_cost())
        
        return card

    def create_cart_section(self, parent):
        # Total cost display
        total_frame = tk.Frame(parent, bg=CARD_BG, relief="raised", bd=1)
        total_frame.pack(fill="x", padx=10, pady=10)
        
        self.total_label = tk.Label(total_frame, text="Total: Rs 0.00", 
                                   font=("Arial", 16, "bold"), bg=CARD_BG, fg=PRIMARY_COLOR)
        self.total_label.pack(pady=15)

        # Denominations
        denom_frame = tk.LabelFrame(parent, text="💰 Insert Money", 
                                   font=("Arial", 10, "bold"), bg=BG_COLOR)
        denom_frame.pack(fill="x", padx=10, pady=10)
        
        self.denom_vars = {}
        for i, denom in enumerate(VALID_DENOMINATIONS):
            frame = tk.Frame(denom_frame, bg=BG_COLOR)
            frame.pack(fill="x", padx=5, pady=2)
            
            tk.Label(frame, text=f"Rs {denom}:", width=8, 
                    bg=BG_COLOR, font=("Arial", 9)).pack(side="left")
            
            var = tk.IntVar(value=0)
            spinbox = tk.Spinbox(frame, from_=0, to=20, textvariable=var, 
                               width=5, font=("Arial", 9))
            spinbox.pack(side="right")
            
            self.denom_vars[denom] = var

        # Purchase button
        purchase_frame = tk.Frame(parent, bg=BG_COLOR)
        purchase_frame.pack(fill="x", padx=10, pady=20)
        
        self.purchase_btn = self.create_styled_button(purchase_frame, "🚀 PURCHASE NOW", 
                                                    self.process_purchase, bg=SUCCESS_COLOR, 
                                                    width=25, height=3)
        self.purchase_btn.pack(fill="x")

        # Cart items display
        cart_items_frame = tk.LabelFrame(parent, text="📋 Selected Items", 
                                       font=("Arial", 10, "bold"), bg=BG_COLOR)
        cart_items_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.cart_text = tk.Text(cart_items_frame, height=8, width=30, 
                                font=("Arial", 9), state="disabled", wrap=tk.WORD)
        scrollbar = tk.Scrollbar(cart_items_frame, command=self.cart_text.yview)
        self.cart_text.configure(yscrollcommand=scrollbar.set)
        
        self.cart_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def update_total_cost(self):
        self.total_cost = sum(self.cart[prod['id']].get() * prod['price'] for prod in self.products)
        self.total_label.config(text=f"Total: Rs {self.total_cost:.2f}")
        self.update_cart_display()

    def update_cart_display(self):
        self.cart_text.config(state="normal")
        self.cart_text.delete(1.0, tk.END)
        
        has_items = False
        for prod in self.products:
            qty = self.cart[prod['id']].get()
            if qty > 0:
                has_items = True
                self.cart_text.insert(tk.END, f"• {prod['name']} x{qty}\n")
                self.cart_text.insert(tk.END, f"  Rs {prod['price'] * qty:.2f}\n\n")
        
        if not has_items:
            self.cart_text.insert(tk.END, "No items selected\n")
            self.cart_text.insert(tk.END, "Click on products to add them!")
        
        self.cart_text.config(state="disabled")

    def refresh_student(self):
        if not self.fetch_products(show_errors=True):
            return
        self.show_student_interface()

    def process_purchase(self):
        selected_items = []
        total_cost = 0
        
        # Validate items and quantities
        for prod in self.products:
            qty = self.cart[prod['id']].get()
            if qty > 0:
                if qty > prod['quantity']:
                    messagebox.showwarning("Stock Issue", 
                                         f"Not enough stock for {prod['name']}\nAvailable: {prod['quantity']}")
                    return
                selected_items.append({"product": prod['id'], "quantity": qty})
                total_cost += prod['price'] * qty

        if not selected_items:
            messagebox.showwarning("Empty Cart", "Please select items to purchase")
            return

        # Calculate money inserted
        money_inserted = 0
        for denom, var in self.denom_vars.items():
            try:
                count = var.get()
                if count < 0:
                    messagebox.showerror("Invalid Input", f"Please enter valid quantity for Rs {denom}")
                    return
                money_inserted += count * denom
            except tk.TclError:
                messagebox.showerror("Invalid Input", f"Please enter valid number for Rs {denom}")
                return

        if money_inserted < total_cost:
            deficit = total_cost - money_inserted
            messagebox.showerror("Insufficient Funds", 
                               f"Insert Rs {deficit:.2f} more\n\nTotal: Rs {total_cost:.2f}\nInserted: Rs {money_inserted:.2f}")
            return

        # Prepare purchase payload
        payload = {
            "customer": self.student_name,
            "items": selected_items,
            "deposited_amount": money_inserted
        }

        try:
            print(f"Sending purchase request: {payload}")  # Debug
            response = requests.post(API_PURCHASE, json=payload, timeout=10)
            print(f"Response status: {response.status_code}")  # Debug
            print(f"Response content: {response.text}")  # Debug
            
            if response.status_code not in [200, 201]:
                error_data = response.json()
                error_msg = error_data.get('error', 'Purchase failed')
                messagebox.showerror("Purchase Failed", f"Error: {error_msg}")
                self.refresh_student()
                return

            data = response.json()
            change = data.get('change_returned', 0)
            
            # Build receipt
            receipt_lines = ["🎉 PURCHASE SUCCESSFUL!\n"]
            receipt_lines.append("=" * 40)
            for prod in self.products:
                qty = self.cart[prod['id']].get()
                if qty > 0:
                    receipt_lines.append(f"{prod['name']} x{qty}")
                    receipt_lines.append(f"  Rs {prod['price'] * qty:.2f}")
            receipt_lines.append("=" * 40)
            receipt_lines.append(f"TOTAL: Rs {total_cost:.2f}")
            receipt_lines.append(f"PAID: Rs {money_inserted:.2f}")
            receipt_lines.append(f"CHANGE: Rs {change:.2f}")
            receipt_lines.append("\nThank you! 👋")
            
            messagebox.showinfo("Purchase Complete", "\n".join(receipt_lines))

            # Reset everything
            for var in self.cart.values():
                var.set(0)
            for var in self.denom_vars.values():
                var.set(0)
            self.update_total_cost()
            self.refresh_student()

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Connection Error", 
                               f"Cannot process purchase:\n{str(e)}")

    # ---------- Admin ----------
    def admin_login(self):
        self.clear_frame()
        password = simpledialog.askstring("Admin Authentication", 
                                         "Enter admin password:", show='*', parent=self.root)
        if password != "admin123":  # Change this password as needed
            messagebox.showerror("Access Denied", "Invalid admin password")
            self.show_role_selection()
            return
        self.show_admin_dashboard()

    def show_admin_dashboard(self):
        self.clear_frame()
        
        # Header
        header_frame = tk.Frame(self.main_frame, bg=HEADER_BG)
        header_frame.pack(fill="x", pady=(0, 20))
        
        tk.Label(header_frame, text="⚙️ Admin Dashboard", 
                font=("Arial", 16, "bold"), bg=HEADER_BG, fg=HEADER_FG).pack(side="left", padx=15, pady=10)
        
        button_frame = tk.Frame(header_frame, bg=HEADER_BG)
        button_frame.pack(side="right", padx=10, pady=5)
        
        self.create_styled_button(button_frame, "🔄 Refresh", self.refresh_admin, 
                                 bg=INFO_COLOR, width=12).pack(side="left", padx=5)
        self.create_styled_button(button_frame, "⬅ Back", self.show_role_selection, 
                                 bg=ACCENT_COLOR, width=10).pack(side="left", padx=5)

        # Notebook for tabs
        notebook = ttk.Notebook(self.main_frame)
        notebook.pack(fill="both", expand=True, pady=10)

        # Products Management Tab
        products_frame = tk.Frame(notebook, bg=BG_COLOR)
        notebook.add(products_frame, text="📦 Products Management")
        self.setup_products_management(products_frame)

        # Transactions Tab
        transactions_frame = tk.Frame(notebook, bg=BG_COLOR)
        notebook.add(transactions_frame, text="📊 Transaction Logs")
        self.setup_transactions_view(transactions_frame)

        self.refresh_admin()

    def setup_products_management(self, parent):
        # Control buttons frame
        control_frame = tk.Frame(parent, bg=BG_COLOR)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        self.create_styled_button(control_frame, "➕ Add Product", self.add_product,
                                 bg=SUCCESS_COLOR, width=15).pack(side="left", padx=5)
        self.create_styled_button(control_frame, "✏️ Edit Product", self.edit_product,
                                 bg=WARNING_COLOR, width=15).pack(side="left", padx=5)
        self.create_styled_button(control_frame, "🗑️ Delete Product", self.delete_product,
                                 bg=ACCENT_COLOR, width=15).pack(side="left", padx=5)
        self.create_styled_button(control_frame, "🔄 Refresh", lambda: self.refresh_products(),
                                 bg=INFO_COLOR, width=15).pack(side="left", padx=5)

        # Products treeview
        tree_frame = tk.Frame(parent, bg=BG_COLOR)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("ID", "Name", "Price", "Quantity", "Category", "Available")
        self.product_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.product_tree.heading(col, text=col)
            self.product_tree.column(col, width=100)
        
        self.product_tree.column("Name", width=150)
        self.product_tree.column("Category", width=120)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.product_tree.yview)
        self.product_tree.configure(yscrollcommand=scrollbar.set)
        
        self.product_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def setup_transactions_view(self, parent):
        # Transactions treeview
        tree_frame = tk.Frame(parent, bg=BG_COLOR)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("ID", "Customer", "Total", "Deposited", "Change", "Items", "Date")
        self.admin_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
        
        # Configure columns
        col_widths = {"ID": 60, "Customer": 120, "Total": 80, "Deposited": 80, 
                     "Change": 80, "Items": 200, "Date": 150}
        
        for col in columns:
            self.admin_tree.heading(col, text=col)
            self.admin_tree.column(col, width=col_widths.get(col, 100))

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.admin_tree.yview)
        self.admin_tree.configure(yscrollcommand=scrollbar.set)
        
        self.admin_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def refresh_admin(self):
        self.refresh_products()
        self.refresh_transactions()

    def refresh_products(self):
        if not self.product_tree:
            return
            
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
            
        if not self.fetch_products(show_errors=True):
            return
            
        for prod in self.products:
            self.product_tree.insert("", "end", values=(
                prod['id'],
                prod['name'],
                f"Rs {prod['price']:.2f}",
                prod['quantity'],
                prod['category'],
                "Yes" if prod['is_available'] else "No"
            ))

    def refresh_transactions(self):
        if not self.admin_tree:
            return
            
        for item in self.admin_tree.get_children():
            self.admin_tree.delete(item)
            
        try:
            response = requests.get(API_TRANSACTIONS, timeout=10)
            response.raise_for_status()
            transactions = response.json()
            
            for trans in transactions:
                # Format items
                items_text = ", ".join([f"{item.get('product_name', 'Unknown')} x{item.get('quantity', 0)}" 
                                      for item in trans.get('items', [])])
                
                # Format timestamp
                timestamp = trans.get('timestamp', '')
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        timestamp = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        pass
                
                self.admin_tree.insert("", "end", values=(
                    trans.get('id', ''),
                    trans.get('customer', ''),
                    f"Rs {trans.get('total_amount', 0):.2f}",
                    f"Rs {trans.get('deposited_amount', 0):.2f}",
                    f"Rs {trans.get('change_returned', 0):.2f}",
                    items_text,
                    timestamp
                ))
                
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Connection Error", 
                               f"Cannot fetch transactions:\n{str(e)}")

    def add_product(self):
        self.show_product_dialog()

    def edit_product(self):
        selection = self.product_tree.selection()
        if not selection:
            messagebox.showwarning("Selection Required", "Please select a product to edit")
            return
            
        item = self.product_tree.item(selection[0])
        product_id = item['values'][0]
        
        # Find product data
        product_data = None
        for prod in self.products:
            if prod['id'] == product_id:
                product_data = prod
                break
                
        if product_data:
            self.show_product_dialog(product_data)

    def delete_product(self):
        selection = self.product_tree.selection()
        if not selection:
            messagebox.showwarning("Selection Required", "Please select a product to delete")
            return
            
        item = self.product_tree.item(selection[0])
        product_name = item['values'][1]
        product_id = item['values'][0]
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{product_name}'?"):
            try:
                response = requests.delete(f"{API_PRODUCTS}{product_id}/", timeout=5)
                if response.status_code == 204:
                    messagebox.showinfo("Success", f"Product '{product_name}' deleted successfully")
                    self.refresh_products()
                else:
                    messagebox.showerror("Error", f"Failed to delete product: {response.text}")
            except requests.exceptions.RequestException as e:
                messagebox.showerror("Connection Error", f"Cannot delete product:\n{str(e)}")

    def show_product_dialog(self, product_data=None):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Product" if not product_data else "Edit Product")
        dialog.geometry("400x350")
        dialog.configure(bg=BG_COLOR)
        dialog.transient(self.root)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog, text="Product Name:", bg=BG_COLOR, font=("Arial", 9)).pack(pady=5)
        name_var = tk.StringVar(value=product_data['name'] if product_data else "")
        name_entry = tk.Entry(dialog, textvariable=name_var, width=40, font=("Arial", 9))
        name_entry.pack(pady=5)

        tk.Label(dialog, text="Price (Rs):", bg=BG_COLOR, font=("Arial", 9)).pack(pady=5)
        price_var = tk.StringVar(value=str(product_data['price']) if product_data else "0.00")
        price_entry = tk.Entry(dialog, textvariable=price_var, width=40, font=("Arial", 9))
        price_entry.pack(pady=5)

        tk.Label(dialog, text="Quantity:", bg=BG_COLOR, font=("Arial", 9)).pack(pady=5)
        quantity_var = tk.StringVar(value=str(product_data['quantity']) if product_data else "0")
        quantity_entry = tk.Entry(dialog, textvariable=quantity_var, width=40, font=("Arial", 9))
        quantity_entry.pack(pady=5)

        tk.Label(dialog, text="Category:", bg=BG_COLOR, font=("Arial", 9)).pack(pady=5)
        category_var = tk.StringVar(value=product_data['category'] if product_data else "")
        category_entry = tk.Entry(dialog, textvariable=category_var, width=40, font=("Arial", 9))
        category_entry.pack(pady=5)

        available_var = tk.BooleanVar(value=product_data['is_available'] if product_data else True)
        tk.Checkbutton(dialog, text="Available", variable=available_var, bg=BG_COLOR, font=("Arial", 9)).pack(pady=10)

        def save_product():
            try:
                data = {
                    "product_name": name_var.get(),
                    "cost": float(price_var.get()),
                    "available_quantity": int(quantity_var.get()),
                    "category": category_var.get(),
                    "is_available": available_var.get()
                }

                if product_data:
                    # Update existing product
                    response = requests.put(f"{API_PRODUCTS}{product_data['id']}/", json=data, timeout=10)
                else:
                    # Create new product
                    response = requests.post(API_PRODUCTS, json=data, timeout=10)

                if response.status_code in [200, 201]:
                    messagebox.showinfo("Success", "Product saved successfully")
                    dialog.destroy()
                    self.refresh_products()
                else:
                    error_msg = response.json().get('error', 'Failed to save product')
                    messagebox.showerror("Error", f"Failed to save product: {error_msg}")
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid numbers for price and quantity")
            except requests.exceptions.RequestException as e:
                messagebox.showerror("Connection Error", f"Cannot save product:\n{str(e)}")

        button_frame = tk.Frame(dialog, bg=BG_COLOR)
        button_frame.pack(pady=20)

        self.create_styled_button(button_frame, "💾 Save", save_product,
                                 bg=SUCCESS_COLOR, width=15).pack(side="left", padx=10)
        self.create_styled_button(button_frame, "❌ Cancel", dialog.destroy,
                                 bg=ACCENT_COLOR, width=15).pack(side="left", padx=10)

# ---------- RUN ----------
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1200x800")
    root.configure(bg=BG_COLOR)
    
    # Center window
    root.update_idletasks()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    window_width = 1200
    window_height = 800
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    app = VendingGUI(root)
    root.mainloop()

