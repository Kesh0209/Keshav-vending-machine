from django.contrib import admin
from django.utils import timezone
from .models import (
    VendingProduct, 
    CustomerSession, 
    PurchaseRecord, 
    MoneyTransaction
)


# Time for Mauritius (+4)

from datetime import timedelta
MAURITIUS_OFFSET = timedelta(hours=4)

def mauritius_time(obj):
    """Convert time to Mauritius timezone"""
    return (obj.timestamp + MAURITIUS_OFFSET).strftime('%d/%m/%Y %H:%M:%S')
mauritius_time.short_description = 'Mauritius Time'


# Admin config

@admin.register(VendingProduct)
class VendingProductAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'category', 'cost', 'available_quantity', 'is_available']
    list_filter = ['category', 'is_available']
    search_fields = ['product_name']
    list_editable = ['cost', 'available_quantity', 'is_available']
    ordering = ['category', 'product_name']

    fieldsets = (
        ('Product Information', {
            'fields': ('product_name', 'category', 'cost', 'product_image')
        }),
        ('Inventory Management', {
            'fields': ('available_quantity', 'is_available')
        }),
    )





class PurchaseRecordInline(admin.TabularInline):
    model = PurchaseRecord
    extra = 0
    readonly_fields = ['formatted_timestamp']
    fields = ['product', 'quantity', 'total_price', 'transaction_type', 'formatted_timestamp']
    can_delete = False

    def formatted_timestamp(self, obj):
        return mauritius_time(obj)
    formatted_timestamp.short_description = 'Purchase Time'

    def has_add_permission(self, request, obj=None):
        return False





class MoneyTransactionInline(admin.TabularInline):
    model = MoneyTransaction
    extra = 0
    readonly_fields = ['get_amount']
    fields = ['type', 'denomination', 'count', 'get_amount']
    can_delete = False

    def get_amount(self, obj):
        return f"Rs {obj.denomination * obj.count:.2f}"
    get_amount.short_description = 'Amount'

    def has_add_permission(self, request, obj=None):
        return False





@admin.register(CustomerSession)
class CustomerSessionAdmin(admin.ModelAdmin):
    list_display = [
        'customer_id', 
        'formatted_session_time',
        'deposited_amount', 
        'final_total', 
        'returned_change',
        'purchase_count',
        'get_session_total'
    ]
    list_filter = ['session_start']
    search_fields = ['customer_id']
    readonly_fields = ['session_start', 'formatted_session_time']
    ordering = ['-session_start']
    
    inlines = [PurchaseRecordInline, MoneyTransactionInline]

    fieldsets = (
        ('Session Information', {
            'fields': ('customer_id', 'formatted_session_time', 'is_completed')
        }),
        ('Financial Details', {
            'fields': ('deposited_amount', 'final_total', 'returned_change')
        }),
    )

    def formatted_session_time(self, obj):
        return mauritius_time(obj)
    formatted_session_time.short_description = 'Session Time'

    def purchase_count(self, obj):
        return obj.transactions.count()
    purchase_count.short_description = 'Items Purchased'

    def get_session_total(self, obj):
        return f"Rs {obj.final_total:.2f}"
    get_session_total.short_description = 'Session Total'





@admin.register(PurchaseRecord)
class PurchaseRecordAdmin(admin.ModelAdmin):
    list_display = [
        'get_customer_name',
        'product', 
        'quantity', 
        'total_price', 
        'transaction_type', 
        'formatted_timestamp'
    ]
    list_filter = ['transaction_type', 'timestamp']
    search_fields = ['product__product_name', 'customer_session__customer_id']
    readonly_fields = ['formatted_timestamp']
    date_hierarchy = 'timestamp'

    def get_customer_name(self, obj):
        return obj.customer_session.customer_id
    get_customer_name.short_description = 'Customer'
    get_customer_name.admin_order_field = 'customer_session__customer_id'

    def formatted_timestamp(self, obj):
        return mauritius_time(obj)
    formatted_timestamp.short_description = 'Purchase Time'
    formatted_timestamp.admin_order_field = 'timestamp'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False





@admin.register(MoneyTransaction)
class MoneyTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'get_customer_name',
        'type',
        'denomination', 
        'count',
        'get_total_amount',
        'formatted_timestamp'
    ]
    list_filter = ['type', 'timestamp']
    search_fields = ['session__customer_id']

    def get_customer_name(self, obj):
        return obj.session.customer_id
    get_customer_name.short_description = 'Customer'
    get_customer_name.admin_order_field = 'session__customer_id'

    def get_total_amount(self, obj):
        return f"Rs {obj.denomination * obj.count:.2f}"
    get_total_amount.short_description = 'Total Amount'

    def formatted_timestamp(self, obj):
        return mauritius_time(obj)
    formatted_timestamp.short_description = 'Transaction Time'
    formatted_timestamp.admin_order_field = 'timestamp'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False




# Admin
admin.site.site_header = "Polytechnic Ebene Vending Machine Administration"
admin.site.site_title = "Vending Machine Admin"
admin.site.index_title = "Welcome to Vending Machine Management"

