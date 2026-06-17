from django.contrib import admin

from .models import (
    AuditLog,
    Branch,
    BranchProductPrice,
    Customer,
    Delivery,
    EmployeeProfile,
    InventoryItem,
    Modifier,
    NotificationRule,
    Order,
    OrderItem,
    OrderItemModifier,
    Payment,
    Product,
    ProductCategory,
    ProductModifier,
    RecipeItem,
    Shift,
    StockBalance,
    StockMovement,
)


class OrderItemModifierInline(admin.TabularInline):
    model = OrderItemModifier
    extra = 0


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["product_name", "unit_price"]


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_number", "branch", "status", "source", "service_type", "created_at"]
    list_filter = ["status", "source", "service_type", "branch"]
    search_fields = ["order_number", "customer__phone", "customer__full_name"]
    inlines = [OrderItemInline, PaymentInline]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "sku", "category", "base_price", "is_favorite", "is_active"]
    list_filter = ["category", "is_favorite", "is_active"]
    search_fields = ["name", "sku"]


@admin.register(StockBalance)
class StockBalanceAdmin(admin.ModelAdmin):
    list_display = ["branch", "inventory_item", "quantity", "updated_at"]
    list_filter = ["branch", "inventory_item__kind"]
    search_fields = ["inventory_item__name"]


admin.site.register(Branch)
admin.site.register(EmployeeProfile)
admin.site.register(ProductCategory)
admin.site.register(Modifier)
admin.site.register(ProductModifier)
admin.site.register(BranchProductPrice)
admin.site.register(Customer)
admin.site.register(Shift)
admin.site.register(OrderItemModifier)
admin.site.register(Payment)
admin.site.register(Delivery)
admin.site.register(InventoryItem)
admin.site.register(RecipeItem)
admin.site.register(StockMovement)
admin.site.register(NotificationRule)
admin.site.register(AuditLog)
