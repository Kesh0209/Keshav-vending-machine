from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from decimal import Decimal
import json

from .models import VendingProduct, PurchaseRecord, CustomerSession, MoneyTransaction

# Valid money denominations (in Rs)
VALID_DENOMINATIONS = [5, 10, 20, 25, 50, 100, 200]


# ---------------------------
# PRODUCTS API
# ---------------------------
@csrf_exempt
def products_api(request):
    """List all products or create a new one"""
    if request.method == 'GET':
        products = list(VendingProduct.objects.values(
            'id', 'product_name', 'cost', 'available_quantity', 'category', 'is_available'
        ))
        return JsonResponse(products, safe=False)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_product = VendingProduct.objects.create(
                product_name=data.get('product_name'),
                cost=data.get('cost', 0),
                available_quantity=data.get('available_quantity', 0),
                category=data.get('category', 'snacks'),
                is_available=True
            )
            return JsonResponse({
                "id": new_product.id,
                "product_name": new_product.product_name,
                "cost": float(new_product.cost),
                "available_quantity": new_product.available_quantity,
                "category": new_product.category
            }, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def product_detail_api(request, pk):
    """Retrieve, update, or delete a specific product"""
    try:
        product = VendingProduct.objects.get(pk=pk)
    except VendingProduct.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)

    if request.method == 'GET':
        return JsonResponse({
            "id": product.id,
            "product_name": product.product_name,
            "cost": float(product.cost),
            "available_quantity": product.available_quantity,
            "category": product.category,
            "is_available": product.is_available
        })

    elif request.method in ['PUT', 'PATCH']:
        try:
            data = json.loads(request.body)
            product.product_name = data.get('product_name', product.product_name)
            product.cost = Decimal(data.get('cost', product.cost))
            product.available_quantity = int(data.get('available_quantity', product.available_quantity))
            product.category = data.get('category', product.category)
            product.is_available = data.get('is_available', product.is_available)
            product.save()
            return JsonResponse({"message": "Product updated successfully"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    elif request.method == 'DELETE':
        product.delete()
        return JsonResponse({"message": "Product deleted"}, status=204)


# ---------------------------
# PURCHASE API (single purchase)
# ---------------------------
@csrf_exempt
def purchase_api(request):
    """Handle a purchase request from frontend or Tkinter"""
    if request.method != 'POST':
        return JsonResponse({"error": "POST required"}, status=400)

    try:
        data = json.loads(request.body)
        customer_id = data.get("customer_id")
        product_id = data.get("product_id")
        quantity = int(data.get("quantity", 1))
        deposited_amount = Decimal(data.get("deposited_amount", 0))

        if not customer_id or not product_id:
            return JsonResponse({"error": "Missing required fields"}, status=400)

        product = VendingProduct.objects.get(id=product_id)
        total_cost = Decimal(product.cost) * quantity

        if product.available_quantity < quantity:
            return JsonResponse({"error": "Insufficient stock"}, status=400)

        if deposited_amount < total_cost:
            deficit = total_cost - deposited_amount
            return JsonResponse({"error": f"Insufficient funds. Need Rs {deficit:.2f} more."}, status=400)

        # Calculate change
        change = round(deposited_amount - total_cost, 2)

        # Create session
        session = CustomerSession.objects.create(
            customer_id=customer_id,
            deposited_amount=deposited_amount,
            final_total=total_cost,
            returned_change=change,
            is_completed=True
        )

        # Log purchase
        PurchaseRecord.objects.create(
            customer_session=session,
            product=product,
            quantity=quantity,
            total_price=total_cost,
            transaction_type='purchase'
        )

        # Update product stock
        product.available_quantity -= quantity
        product.save()

        return JsonResponse({
            "message": "Purchase successful",
            "product": product.product_name,
            "quantity": quantity,
            "total_cost": float(total_cost),
            "change_returned": float(change)
        })

    except VendingProduct.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# ---------------------------
# PURCHASE RECORDS API (Admin Dashboard)
# ---------------------------
def purchases_api(request):
    """Return all recorded purchases for admin dashboard"""
    if request.method != 'GET':
        return JsonResponse({"error": "GET required"}, status=400)

    purchases = PurchaseRecord.objects.select_related('customer_session', 'product').order_by('-timestamp')
    data = []
    for p in purchases:
        data.append({
            "customer": p.customer_session.customer_id if p.customer_session else "Unknown",
            "product": p.product.product_name,
            "quantity": p.quantity,
            "total_price": float(p.total_price),
            "deposited_amount": float(p.customer_session.deposited_amount) if p.customer_session else 0,
            "change_returned": float(p.customer_session.returned_change) if p.customer_session else 0,
            "transaction_type": p.transaction_type,
            "timestamp": p.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        })
    return JsonResponse(data, safe=False)


# ---------------------------
# CUSTOMER SESSIONS API
# ---------------------------
def sessions_api(request):
    """Return all customer sessions (admin view)"""
    if request.method != 'GET':
        return JsonResponse({"error": "GET required"}, status=400)

    sessions = CustomerSession.objects.all().order_by('-session_start')
    data = []
    for s in sessions:
        data.append({
            "id": s.id,
            "customer_id": s.customer_id,
            "deposited_amount": float(s.deposited_amount),
            "final_total": float(s.final_total),
            "returned_change": float(s.returned_change),
            "is_completed": s.is_completed,
            "timestamp": s.session_start.strftime("%Y-%m-%d %H:%M:%S")
        })
    return JsonResponse(data, safe=False)


# ---------------------------
# MONEY TRANSACTION LOG (OPTIONAL)
# ---------------------------
def money_transactions_api(request):
    """Return all money transactions (inserted and change)"""
    if request.method != 'GET':
        return JsonResponse({"error": "GET required"}, status=400)

    transactions = MoneyTransaction.objects.select_related('session').order_by('-timestamp')
    data = []
    for t in transactions:
        data.append({
            "session_id": t.session.id,
            "customer": t.session.customer_id,
            "type": t.type,
            "denomination": float(t.denomination),
            "count": t.count,
            "timestamp": t.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        })
    return JsonResponse(data, safe=False)

from django.http import JsonResponse
from .models import PurchaseRecord

def orders_api(request):
    """
    Simple API to fetch all purchase transactions.
    """
    orders = PurchaseRecord.objects.all().values(
        'id', 'product__product_name', 'quantity', 'total_price',
        'transaction_type', 'timestamp', 'customer_session__customer_id'
    )

    return JsonResponse(list(orders), safe=False)
