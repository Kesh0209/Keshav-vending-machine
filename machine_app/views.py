import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from .models import VendingProduct, PurchaseRecord, CustomerSession, MoneyTransaction
from datetime import datetime, timedelta

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

            
            request.session['cart'] = cart
            request.session['total_cost'] = total_cost
            print(f"Cart saved to session: {cart}")

            return render(request, 'machine_app/purchase.html', {
                'cart': cart,
                'total_cost': total_cost,
                'student_name': student_name,
                'denominations': VALID_DENOMINATIONS
            })

        
        elif 'process_payment' in request.POST:
            print("=== PAYMENT PROCESSING DETECTED ===")
            
            
            cart = request.session.get('cart', [])
            total_cost = request.session.get('total_cost', 0)
            
            print("Cart from session:", cart)
            print("Total cost from session:", total_cost)

            if not cart:
                messages.error(request, "❌ Cart is empty. Please select items first.")
                return redirect('products')

            
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

            
            change = round(money_inserted - total_cost, 2)
            print(f"Transaction successful. Change: {change}")

            # Get current Mauritius time (UTC+4)
            # Since Render server is in UTC, we need to add 4 hours for Mauritius time
            mauritius_time = timezone.now() + timedelta(hours=4)
            
            session = CustomerSession.objects.create(
                customer_id=student_name,
                deposited_amount=money_inserted,
                final_total=total_cost,
                returned_change=change,
                session_start=mauritius_time,  # Use Mauritius time
                is_completed=True
            )

            
            for denom, count in inserted.items():
                if count > 0:
                    MoneyTransaction.objects.create(
                        session=session,
                        denomination=denom,
                        count=count,
                        type='inserted'
                    )

            
            change_details = {}
            if change > 0:
                remaining = change
                for denom in sorted(VALID_DENOMINATIONS, reverse=True):
                    num = int(remaining // denom)
                    if num > 0:
                        change_details[denom] = num
                        remaining -= denom * num
                        remaining = round(remaining, 2)

                
                for denom, count in change_details.items():
                    MoneyTransaction.objects.create(
                        session=session,
                        denomination=denom,
                        count=count,
                        type='change'
                    )

            
            for item in cart:
                product = VendingProduct.objects.get(id=item['id'])
                qty = item['qty']

                
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

    
    print("No valid POST data detected, redirecting to products")
    return redirect('products')

def logout_view(request):
    request.session.flush()
    messages.success(request, "You have been logged out successfully.")
    return redirect('index')

from django.http import JsonResponse
from .models import VendingProduct

def products_api(request):
    product_list = list(VendingProduct.objects.values('id', 'product_name', 'cost', 'available_quantity'))
    
    for p in product_list:
        p['name'] = p.pop('product_name')
        p['price'] = float(p.pop('cost'))
        p['quantity'] = p.pop('available_quantity')
        if p.get('image'):
            p['image'] = request.build_absolute_uri(settings.MEDIA_URL + str(p['image']))
    return JsonResponse(product_list, safe=False)

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import transaction
import json

# ADD THESE API ENDPOINTS FOR TKINTER
@api_view(['GET'])
def api_products(request):
    """API for Tkinter to get products"""
    products = VendingProduct.objects.filter(is_available=True)
    product_list = []
    for product in products:
        product_list.append({
            'id': product.id,
            'product_name': product.product_name,
            'name': product.product_name,
            'cost': float(product.cost),
            'price': float(product.cost),
            'available_quantity': product.available_quantity,
            'quantity': product.available_quantity,
            'category': product.category,
            'is_available': product.is_available,
            'image': request.build_absolute_uri(product.product_image.url) if product.product_image else None
        })
    return Response(product_list)

@api_view(['POST'])
@transaction.atomic
def api_purchase(request):
    """API for Tkinter to process purchases"""
    try:
        data = request.data
        customer_name = data.get('customer', '').strip()
        items = data.get('items', [])
        deposited_amount = float(data.get('deposited_amount', 0))
        
        if not customer_name:
            return Response({'error': 'Customer name is required'}, status=400)
        
        if not items:
            return Response({'error': 'No items selected'}, status=400)
        
        # Calculate total and process purchase
        total_cost = 0
        purchased_items = []
        
        for item in items:
            product_id = item.get('product')
            quantity = int(item.get('quantity', 0))
            
            if quantity <= 0:
                continue
                
            product = VendingProduct.objects.get(id=product_id)
            
            if product.available_quantity < quantity:
                return Response({'error': f'Not enough stock for {product.product_name}'}, status=400)
            
            item_total = float(product.cost) * quantity
            total_cost += item_total
            
            # Reduce stock
            product.available_quantity -= quantity
            product.save()
            
            purchased_items.append({
                'product_name': product.product_name,
                'quantity': quantity,
                'total': item_total
            })
        
        # Check if enough money was deposited
        if deposited_amount < total_cost:
            return Response({'error': f'Insufficient funds. Need Rs {total_cost - deposited_amount:.2f} more'}, status=400)
        
        change = deposited_amount - total_cost
        
        # Create customer session with Mauritius time (UTC+4)
        mauritius_time = timezone.now() + timedelta(hours=4)
        session = CustomerSession.objects.create(
            customer_id=customer_name,
            deposited_amount=deposited_amount,
            final_total=total_cost,
            returned_change=change,
            session_start=mauritius_time,  # Use Mauritius time
            is_completed=True
        )
        
        # Create purchase records
        for item in purchased_items:
            product = VendingProduct.objects.get(product_name=item['product_name'])
            PurchaseRecord.objects.create(
                customer_session=session,
                product=product,
                quantity=item['quantity'],
                total_price=item['total'],
                transaction_type='purchase'
            )
        
        # Return success response
        return Response({
            'success': True,
            'message': 'Purchase successful',
            'total_amount': total_cost,
            'change_returned': change,
            'items': purchased_items
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@api_view(['GET'])
def api_purchases(request):
    """API for Tkinter to get transaction history"""
    sessions = CustomerSession.objects.filter(is_completed=True).order_by('-session_start')
    transactions = []
    
    for session in sessions:
        purchase_items = PurchaseRecord.objects.filter(
            customer_session=session, 
            transaction_type='purchase'
        )
        
        items_list = []
        for item in purchase_items:
            items_list.append({
                'product_name': item.product.product_name,
                'quantity': item.quantity
            })
        
        # Convert to Mauritius time for display
        mauritius_time = session.session_start + timedelta(hours=4)
        
        transactions.append({
            'id': session.id,
            'customer': session.customer_id,
            'total_amount': float(session.final_total),
            'deposited_amount': float(session.deposited_amount),
            'change_returned': float(session.returned_change),
            'timestamp': mauritius_time,  # Use Mauritius time
            'items': items_list
        })
    
    return Response(transactions)