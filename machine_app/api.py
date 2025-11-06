from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import VendingProduct, CustomerSession, PurchaseRecord, MoneyTransaction
from django.utils import timezone

@csrf_exempt
def purchase_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        customer_id = data.get("customer_id")
        product_id = data.get("product_id")
        quantity = int(data.get("quantity", 0))
        deposited_amount = float(data.get("deposited_amount", 0))

        if not customer_id or not product_id or quantity <= 0 or deposited_amount <= 0:
            return JsonResponse({"error": "Missing or invalid input values."}, status=400)

        try:
            product = VendingProduct.objects.get(id=product_id)
        except VendingProduct.DoesNotExist:
            return JsonResponse({"error": "Product not found."}, status=404)

        if not product.is_available or product.available_quantity < quantity:
            return JsonResponse({"error": "Insufficient stock available."}, status=400)

        total_cost = float(product.cost) * quantity
        if deposited_amount < total_cost:
            return JsonResponse({"error": f"Insufficient funds. Total = Rs {total_cost}"}, status=400)

        session = CustomerSession.objects.create(
            customer_id=customer_id,
            deposited_amount=deposited_amount,
            final_total=total_cost,
            returned_change=deposited_amount - total_cost,
            is_completed=True
        )

        PurchaseRecord.objects.create(
            customer_session=session,
            product=product,
            quantity=quantity,
            total_price=total_cost,
            transaction_type="purchase"
        )

        MoneyTransaction.objects.create(
            session=session,
            denomination=deposited_amount,
            count=1,
            type="inserted"
        )

        if deposited_amount > total_cost:
            MoneyTransaction.objects.create(
                session=session,
                denomination=deposited_amount - total_cost,
                count=1,
                type="change"
            )

        product.available_quantity -= quantity
        if product.available_quantity == 0:
            product.is_available = False
        product.save()

        return JsonResponse({
            "message": "Purchase successful",
            "customer": customer_id,
            "product": product.product_name,
            "quantity": quantity,
            "total_price": total_cost,
            "change_returned": deposited_amount - total_cost
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format."}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


