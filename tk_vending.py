import tkinter as tk
from tkinter import messagebox, simpledialog
import requests

API_PRODUCTS = "http://127.0.0.1:8000/api/products/"
API_PURCHASE = "http://127.0.0.1:8000/api/purchase/"
VALID_DENOMINATIONS = [5, 10, 20, 25, 50, 100, 200]

class VendingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Polytechnic Vending Machine")
        self.student_name = ""
        self.products = []
        self.cart = {}
        self.total_cost = 0
        self.init_gui()

    def init_gui(self):
        self.student_name = simpledialog.askstring("Student Name", "Enter your name:")
        if not self.student_name:
            messagebox.showerror("Error", "Name is required")
            self.root.destroy()
            return

        self.fetch_products()
        self.products_frame = tk.Frame(self.root)
        self.products_frame.pack(padx=10, pady=10)

        self.denominations_frame = tk.Frame(self.root)
        self.denominations_frame.pack(padx=10, pady=10)

        self.total_label = tk.Label(self.root, text=f"Total Cost: Rs {self.total_cost:.2f}")
        self.total_label.pack(pady=5)

        self.update_products_ui()
        self.update_denominations_ui()

    def fetch_products(self):
        try:
            response = requests.get(API_PRODUCTS, timeout=5)
            response.raise_for_status()
            self.products = response.json()
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Cannot connect to Django server")
            self.root.destroy()

    def update_products_ui(self):
        for widget in self.products_frame.winfo_children():
            widget.destroy()

        tk.Label(self.products_frame, text="Product", width=20).grid(row=0, column=0)
        tk.Label(self.products_frame, text="Price", width=10).grid(row=0, column=1)
        tk.Label(self.products_frame, text="Quantity", width=10).grid(row=0, column=2)
        tk.Label(self.products_frame, text="Stock", width=10).grid(row=0, column=3)

        for i, prod in enumerate(self.products):
            btn = tk.Button(self.products_frame, text=prod['name'], width=20,
                            command=lambda p=prod: self.add_to_cart(p))
            btn.grid(row=i+1, column=0)
            tk.Label(self.products_frame, text=f"Rs {prod['price']}", width=10).grid(row=i+1, column=1)
            qty_var = tk.IntVar(value=0)
            tk.Entry(self.products_frame, textvariable=qty_var, width=10).grid(row=i+1, column=2)
            tk.Label(self.products_frame, text=prod['quantity'], width=10).grid(row=i+1, column=3)
            self.cart[prod['id']] = qty_var

        self.purchase_button = tk.Button(self.products_frame, text="Purchase", command=self.process_purchase)
        self.purchase_button.grid(row=len(self.products)+1, column=0, columnspan=4, pady=10)

    def add_to_cart(self, product):
        if self.cart[product['id']].get() < product['quantity']:
            self.cart[product['id']].set(self.cart[product['id']].get() + 1)
            self.update_total_cost()

    def update_total_cost(self):
        self.total_cost = sum(self.cart[prod['id']].get() * prod['price'] for prod in self.products)
        self.total_label.config(text=f"Total Cost: Rs {self.total_cost:.2f}")

    def update_denominations_ui(self):
        for widget in self.denominations_frame.winfo_children():
            widget.destroy()

        tk.Label(self.denominations_frame, text="Insert Money (denominations)").grid(row=0, column=0, columnspan=2)
        self.denom_vars = {}

        for i, denom in enumerate(VALID_DENOMINATIONS):
            tk.Label(self.denominations_frame, text=f"Rs {denom}:", width=10).grid(row=i+1, column=0)
            var = tk.IntVar(value=0)
            tk.Entry(self.denominations_frame, textvariable=var, width=5).grid(row=i+1, column=1)
            self.denom_vars[denom] = var

    def process_purchase(self):
        selected_items = []
        total_cost = 0
        for prod in self.products:
            qty = self.cart[prod['id']].get()
            if qty > 0:
                if qty > prod['quantity']:
                    messagebox.showwarning("Warning", f"Not enough stock for {prod['name']}. Available: {prod['quantity']}")
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
                self.fetch_products()
                self.update_products_ui()
                return
            else:
                items_msg = "\n".join([f"{item['name']} x {item['quantity']}" for item in selected_items])
                change = data.get('change_returned', 0)
                msg = f"Purchase successful!\n{items_msg}\nTotal: Rs {total_cost}\nMoney inserted: Rs {money_inserted}\nChange returned: Rs {change:.2f}"
                messagebox.showinfo("Success", msg)

                self.fetch_products()
                self.update_products_ui()
                for var in self.denom_vars.values():
                    var.set(0)
                for var in self.cart.values():
                    var.set(0)
                self.update_total_cost()
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Cannot connect to Django server")
            return


if __name__ == "__main__":
    root = tk.Tk()
    app = VendingGUI(root)
    root.mainloop()





