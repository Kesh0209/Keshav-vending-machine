import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import requests

API_PRODUCTS = "http://127.0.0.1:8000/api/products/"
API_PURCHASE = "http://127.0.0.1:8000/api/purchase/"
API_TRANSACTIONS = "http://127.0.0.1:8000/api/purchases/"  # example if your endpoint is called purchases
VALID_DENOMINATIONS = [5, 10, 20, 25, 50, 100, 200]

class VendingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Polytechnic Vending Machine")
        self.role = None
        self.student_name = ""
        self.products = []
        self.cart = {}
        self.total_cost = 0
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill="both", expand=True)
        self.show_role_selection()

    # ---------- Role Selection ----------
    def show_role_selection(self):
        self.clear_frame()
        tk.Label(self.main_frame, text="Select Role", font=("Helvetica", 16)).pack(pady=20)
        tk.Button(self.main_frame, text="Student", width=20, height=2, command=self.student_login).pack(pady=10)
        tk.Button(self.main_frame, text="Admin", width=20, height=2, command=self.admin_login).pack(pady=10)

    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    # ---------- Student ----------
    def student_login(self):
        self.clear_frame()
        self.student_name = simpledialog.askstring("Student Name", "Enter your name:")
        if not self.student_name:
            messagebox.showerror("Error", "Name is required")
            self.show_role_selection()
            return
        self.fetch_products()
        self.show_student_interface()

    def fetch_products(self):
        try:
            response = requests.get(API_PRODUCTS, timeout=5)
            response.raise_for_status()
            products = response.json()
            self.products = []
            for p in products:
                self.products.append({
                    "id": p["id"],
                    "name": p["product_name"],
                    "price": float(p["cost"]),
                    "quantity": p["available_quantity"],
                    "category": p.get("category", ""),
                    "is_available": p.get("is_available", True)
                })
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Cannot connect to Django server")
            self.root.destroy()

    def show_student_interface(self):
        self.clear_frame()
        tk.Label(self.main_frame, text=f"Student: {self.student_name}", font=("Helvetica", 14)).pack(pady=10)
        tk.Button(self.main_frame, text="Back", command=self.show_role_selection).pack(anchor="nw", padx=10, pady=5)

        # Product Frame
        self.products_frame = tk.Frame(self.main_frame)
        self.products_frame.pack(padx=10, pady=10)

        self.cart = {}
        self.total_cost = 0

        tk.Label(self.products_frame, text="Product", width=20, bg="#ddd").grid(row=0, column=0)
        tk.Label(self.products_frame, text="Price", width=10, bg="#ddd").grid(row=0, column=1)
        tk.Label(self.products_frame, text="Qty", width=10, bg="#ddd").grid(row=0, column=2)
        tk.Label(self.products_frame, text="Stock", width=10, bg="#ddd").grid(row=0, column=3)

        for i, prod in enumerate(self.products):
            btn = tk.Button(self.products_frame, text=prod['name'], width=20,
                            command=lambda p=prod: self.add_to_cart(p))
            btn.grid(row=i+1, column=0)
            tk.Label(self.products_frame, text=f"Rs {prod['price']}", width=10).grid(row=i+1, column=1)
            qty_var = tk.IntVar(value=0)
            tk.Entry(self.products_frame, textvariable=qty_var, width=10).grid(row=i+1, column=2)
            tk.Label(self.products_frame, text=prod['quantity'], width=10).grid(row=i+1, column=3)
            self.cart[prod['id']] = qty_var

        self.total_label = tk.Label(self.main_frame, text=f"Total: Rs {self.total_cost:.2f}", font=("Helvetica", 14))
        self.total_label.pack(pady=5)

        # Denominations
        self.denominations_frame = tk.Frame(self.main_frame)
        self.denominations_frame.pack(pady=10)
        tk.Label(self.denominations_frame, text="Insert Money").grid(row=0, column=0, columnspan=2)
        self.denom_vars = {}
        for i, denom in enumerate(VALID_DENOMINATIONS):
            tk.Label(self.denominations_frame, text=f"Rs {denom}:", width=10).grid(row=i+1, column=0)
            var = tk.IntVar(value=0)
            tk.Entry(self.denominations_frame, textvariable=var, width=5).grid(row=i+1, column=1)
            self.denom_vars[denom] = var

        tk.Button(self.main_frame, text="Purchase", command=self.process_purchase).pack(pady=10)
        tk.Button(self.main_frame, text="Refresh Products", command=self.refresh_student).pack(pady=5)

    def add_to_cart(self, product):
        if self.cart[product['id']].get() < product['quantity']:
            self.cart[product['id']].set(self.cart[product['id']].get() + 1)
            self.update_total_cost()

    def update_total_cost(self):
        self.total_cost = sum(self.cart[prod['id']].get() * prod['price'] for prod in self.products)
        self.total_label.config(text=f"Total: Rs {self.total_cost:.2f}")

    def refresh_student(self):
        self.fetch_products()
        self.show_student_interface()

    def process_purchase(self):
        selected_items = []
        total_cost = 0
        for prod in self.products:
            qty = self.cart[prod['id']].get()
            if qty > 0:
                if qty > prod['quantity']:
                    messagebox.showwarning("Warning", f"Not enough stock for {prod['name']}")
                    return
                selected_items.append({"product_id": prod['id'], "name": prod['name'], "quantity": qty, "price": prod['price']})
                total_cost += prod['price'] * qty

        if not selected_items:
            messagebox.showwarning("Warning", "No items selected")
            return

        money_inserted = sum(var.get() * denom for denom, var in self.denom_vars.items())
        if money_inserted < total_cost:
            deficit = total_cost - money_inserted
            messagebox.showerror("Error", f"Insufficient funds! Insert Rs {deficit:.2f} more")
            return

        payload = {
            "customer_id": self.student_name,
            "product_id": selected_items[0]['product_id'],
            "quantity": selected_items[0]['quantity'],
            "deposited_amount": money_inserted
        }

        try:
            response = requests.post(API_PURCHASE, json=payload, timeout=5)
            data = response.json()
            if "error" in data:
                messagebox.showerror("Error", data["error"])
                self.refresh_student()
                return
            else:
                change = data.get('change_returned', 0)
                items_msg = "\n".join([f"{item['name']} x {item['quantity']}" for item in selected_items])
                messagebox.showinfo("Success", f"Purchase successful!\n{items_msg}\nTotal: Rs {total_cost}\nMoney inserted: Rs {money_inserted}\nChange returned: Rs {change:.2f}")
                self.refresh_student()
                for var in self.denom_vars.values():
                    var.set(0)
                for var in self.cart.values():
                    var.set(0)
                self.update_total_cost()
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Cannot connect to Django server")
            return

    # ---------- Admin ----------
    def admin_login(self):
        self.clear_frame()
        tk.Label(self.main_frame, text="Admin Dashboard", font=("Helvetica", 16)).pack(pady=10)
        tk.Button(self.main_frame, text="Back", command=self.show_role_selection).pack(anchor="nw", padx=10, pady=5)
        self.show_admin_dashboard()

    def show_admin_dashboard(self):
        self.clear_frame()
        tk.Label(self.main_frame, text="Admin Dashboard", font=("Helvetica", 16)).pack(pady=10)
        tk.Button(self.main_frame, text="Back", command=self.show_role_selection).pack(anchor="nw", padx=10, pady=5)
        self.admin_tree = ttk.Treeview(self.main_frame, columns=("ID", "Name", "Price", "Qty", "Category"), show="headings")
        for col in ("ID", "Name", "Price", "Qty", "Category"):
            self.admin_tree.heading(col, text=col)
        self.admin_tree.pack(padx=10, pady=10)

        btn_frame = tk.Frame(self.main_frame)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Add Product", command=self.admin_add_product).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Update Product", command=self.admin_update_product).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Delete Product", command=self.admin_delete_product).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Refresh", command=self.refresh_admin).pack(side="left", padx=5)
        tk.Button(btn_frame, text="View Transactions", command=self.admin_transactions).pack(side="left", padx=5)

        self.refresh_admin()

    def refresh_admin(self):
        self.fetch_products()
        for i in self.admin_tree.get_children():
            self.admin_tree.delete(i)
        for p in self.products:
            self.admin_tree.insert("", "end", values=(p["id"], p["name"], p["price"], p["quantity"], p["category"]))

    def admin_add_product(self):
        self.admin_edit_product()

    def admin_update_product(self):
        selected = self.admin_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a product to update")
            return
        values = self.admin_tree.item(selected[0])['values']
        self.admin_edit_product(values)

    def admin_delete_product(self):
        selected = self.admin_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a product to delete")
            return
        values = self.admin_tree.item(selected[0])['values']
        product_id = values[0]
        try:
            response = requests.delete(f"{API_PRODUCTS}{product_id}/")
            if response.status_code in [200, 204]:
                messagebox.showinfo("Deleted", "Product deleted successfully")
                self.refresh_admin()
            else:
                messagebox.showerror("Error", "Failed to delete product")
        except:
            messagebox.showerror("Error", "Cannot connect to Django server")

    def admin_edit_product(self, product_values=None):
        popup = tk.Toplevel()
        popup.title("Product Editor")
        fields = ["Name", "Price", "Quantity", "Category"]
        entries = {}
        for i, field in enumerate(fields):
            tk.Label(popup, text=field).grid(row=i, column=0, padx=5, pady=5)
            entry = tk.Entry(popup)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entries[field] = entry

        if product_values:
            entries["Name"].insert(0, product_values[1])
            entries["Price"].insert(0, product_values[2])
            entries["Quantity"].insert(0, product_values[3])
            entries["Category"].insert(0, product_values[4])

        def save_product():
            data = {
                "product_name": entries["Name"].get(),
                "cost": entries["Price"].get(),
                "available_quantity": entries["Quantity"].get(),
                "category": entries["Category"].get()
            }
            try:
                if product_values:  # update
                    product_id = product_values[0]
                    response = requests.put(f"{API_PRODUCTS}{product_id}/", json=data)
                else:  # create
                    response = requests.post(API_PRODUCTS, json=data)
                if response.status_code in [200, 201]:
                    messagebox.showinfo("Saved", "Product saved successfully")
                    popup.destroy()
                    self.refresh_admin()
                else:
                    messagebox.showerror("Error", "Failed to save product")
            except:
                messagebox.showerror("Error", "Cannot connect to Django server")

        tk.Button(popup, text="Save", command=save_product).grid(row=len(fields), column=0, columnspan=2, pady=10)

    def admin_transactions(self):
        try:
            response = requests.get(API_TRANSACTIONS)
            response.raise_for_status()
            data = response.json()
        except:
            messagebox.showerror("Error", "Cannot fetch transactions")
            return

        popup = tk.Toplevel()
        popup.title("Transactions Log")
        tree = ttk.Treeview(popup, columns=("Customer", "Product", "Quantity", "Total Price", "Inserted Money", "Change"), show="headings")
        for col in ("Customer", "Product", "Quantity", "Total Price", "Inserted Money", "Change"):
            tree.heading(col, text=col)
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        for row in data:
            tree.insert("", "end", values=(
                row.get("customer"),
                row.get("product"),
                row.get("quantity"),
                row.get("total_price"),
                row.get("deposited_amount"),
                row.get("change_returned")
            ))

if __name__ == "__main__":
    root = tk.Tk()
    app = VendingGUI(root)
    root.mainloop()












