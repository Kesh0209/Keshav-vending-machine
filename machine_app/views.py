import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from .models import VendingProduct, PurchaseRecord, CustomerSession, MoneyTransaction

# Available currency denominations
VALID_DENOMINATIONS = [5, 10, 20, 25, 50, 100, 200]

def index(request):
    if request.method == 'POST':
        role = request.POST.get('role')
        if role == 'admin':
            return redirect('/admin/')
        elif role == 'student':
            request.session.flush()
            request.session['role'] = 'student'
            return redirect('enter_name')
    return render(request, 'machine_app/index.html')

def enter_name(request):
    if request.session.get('student_name'):
        return redirect('vending')

    if request.method == 'POST':
        name = request.POST.get('student_name', '').strip()
        if name:
            request.session['student_name'] = name
            return redirect('vending')
        else:
            messages.error(request, "Please enter your name.")

    return render(request, 'machine_app/enter_name.html')

def vending_machine(request):
    role = request.session.get('role')
    student_name = request.session.get('student_name')
    if role != 'student' or not student_name:
        return redirect('index')

    products = VendingProduct.objects.all()
    return render(request, 'machine_app/vending_machine.html', {
        "products": products,
        "MEDIA_URL": settings.MEDIA_URL,
        "student_name": student_name
    })

def products(request):
    role = request.session.get('role')
    student_name = request.session.get('student_name')
    if role != 'student' or not student_name:
        return redirect('index')

    # Filter products by category
    snacks = VendingProduct.objects.filter(category='snacks', is_available=True)
    drinks = VendingProduct.objects.filter(category='drinks', is_available=True)
    
    return render(request, 'machine_app/products.html', {
        'snacks': snacks,
        'drinks': drinks,
        'student_name': student_name
    })

@transaction.atomic
def purchase(request):
    student_name = request.session.get('student_name', '')
    if not student_name:
        return redirect('enter_name')

    if request.method == 'POST':
        print("=== PURCHASE POST REQUEST ===")
        print("POST keys:", list(request.POST.keys()))
        
        # Step 1: Cart submitted from products page
        if 'cart_submitted' in request.POST:
            print("=== CART SUBMISSION DETECTED ===")
            cart = []
            total_cost = 0
            for key, value in request.POST.items():
                if key.startswith('qty_'):
                    try:
                        prod_id = int(key.split('_')[1])
                        qty = int(value)
                    except (ValueError, IndexError):
                        continue
                    if qty > 0:
                        product = VendingProduct.objects.get(id=prod_id)
                        item_total = float(product.cost) * qty
                        cart.append({
                            'id': prod_id,
                            'name': product.product_name,
                            'price': float(product.cost),
                            'qty': qty,
                            'total_price': item_total
                        })
                        total_cost += item_total

            if not cart:
                messages.error(request, "Your cart is empty!")
                return redirect('products')

            # Store cart in session
            request.session['cart'] = cart
            request.session['total_cost'] = total_cost
            print(f"Cart saved to session: {cart}")

            return render(request, 'machine_app/purchase.html', {
                'cart': cart,
                'total_cost': total_cost,
                'student_name': student_name,
                'denominations': VALID_DENOMINATIONS
            })

        # Step 2: Money inserted from purchase page
        elif 'process_payment' in request.POST:
            print("=== PAYMENT PROCESSING DETECTED ===")
            
            # Get cart from session instead of form data
            cart = request.session.get('cart', [])
            total_cost = request.session.get('total_cost', 0)
            
            print("Cart from session:", cart)
            print("Total cost from session:", total_cost)

            if not cart:
                messages.error(request, "❌ Cart is empty. Please select items first.")
                return redirect('products')

            # Process inserted money
            inserted = {}
            money_inserted = 0
            for denom in VALID_DENOMINATIONS:
                try:
                    count = int(request.POST.get(f'insert_{denom}', 0))
                except ValueError:
                    count = 0
                inserted[denom] = count
                money_inserted += denom * count

            print(f"Money inserted: {money_inserted}")

            # Check if enough money was inserted
            if money_inserted < total_cost:
                deficit = total_cost - money_inserted
                print(f"Insufficient funds: {deficit} deficit")
                return render(request, 'machine_app/purchase.html', {
                    'cart': cart,
                    'total_cost': total_cost,
                    'student_name': student_name,
                    'money_inserted': money_inserted,
                    'denominations': VALID_DENOMINATIONS,
                    'insufficient': f"❌ Not enough money! Please insert at least Rs {deficit:.2f} more."
                })

            # Enough money → process transaction
            change = round(money_inserted - total_cost, 2)
            print(f"Transaction successful. Change: {change}")

            # Create customer session
            session = CustomerSession.objects.create(
                customer_id=student_name,
                deposited_amount=money_inserted,
                final_total=total_cost,
                returned_change=change,
                is_completed=True
            )

            # Record inserted money
            for denom, count in inserted.items():
                if count > 0:
                    MoneyTransaction.objects.create(
                        session=session,
                        denomination=denom,
                        count=count,
                        type='inserted'
                    )

            # Calculate change breakdown
            change_details = {}
            if change > 0:
                remaining = change
                for denom in sorted(VALID_DENOMINATIONS, reverse=True):
                    num = int(remaining // denom)
                    if num > 0:
                        change_details[denom] = num
                        remaining -= denom * num
                        remaining = round(remaining, 2)

                # Record change given
                for denom, count in change_details.items():
                    MoneyTransaction.objects.create(
                        session=session,
                        denomination=denom,
                        count=count,
                        type='change'
                    )

            # Process each cart item and update stock
            for item in cart:
                product = VendingProduct.objects.get(id=item['id'])
                qty = item['qty']

                # Handle low stock by auto-restocking
                if product.available_quantity < qty:
                    refill_qty = 30 - product.available_quantity
                    if refill_qty > 0:
                        PurchaseRecord.objects.create(
                            customer_session=session,
                            product=product,
                            quantity=refill_qty,
                            total_price=0,
                            transaction_type='refill'
                        )
                        product.available_quantity = 30
                        product.save()

                # Process the actual purchase
                if product.available_quantity >= qty:
                    product.available_quantity -= qty
                    product.save()

                    PurchaseRecord.objects.create(
                        customer_session=session,
                        product=product,
                        quantity=qty,
                        total_price=float(product.cost) * qty,
                        transaction_type='purchase'
                    )
                else:
                    messages.warning(request, f"Insufficient stock for {product.product_name}")

            # Clear cart from session after successful purchase
            if 'cart' in request.session:
                del request.session['cart']
            if 'total_cost' in request.session:
                del request.session['total_cost']

            # Success page
            return render(request, 'machine_app/success.html', {
                'cart': cart,
                'student_name': student_name,
                'total_cost': total_cost,
                'money_inserted': money_inserted,
                'change': change,
                'change_details': change_details,
                'session': session,
            })

    # If GET request or no valid POST data, redirect to products
    print("No valid POST data detected, redirecting to products")
    return redirect('products')

def logout_view(request):
    request.session.flush()
    messages.success(request, "You have been logged out successfully.")
    return redirect('index')