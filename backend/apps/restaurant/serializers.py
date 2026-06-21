from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
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

User = get_user_model()


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = "__all__"


class EmployeeProfileSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)

    class Meta:
        model = EmployeeProfile
        fields = "__all__"


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = "__all__"


class ModifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modifier
        fields = "__all__"


class ProductModifierSerializer(serializers.ModelSerializer):
    modifier = ModifierSerializer(read_only=True)

    class Meta:
        model = ProductModifier
        fields = ["id", "modifier", "is_default"]


class BranchProductPriceSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = BranchProductPrice
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    available_modifiers = ProductModifierSerializer(many=True, read_only=True)
    branch_prices = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = "__all__"

    def get_branch_prices(self, obj: Product):
        request = self.context.get("request")
        queryset = obj.branch_prices.all()
        if request and request.user.is_authenticated:
            requested_branch = request.query_params.get("branch")
            if requested_branch:
                queryset = queryset.filter(branch_id=requested_branch)
                return BranchProductPriceSerializer(queryset, many=True, context=self.context).data
        if request and request.user.is_authenticated and not request.user.is_superuser:
            profile = getattr(request.user, "employee_profile", None)
            can_see_all = profile and profile.is_active and profile.role in {
                EmployeeProfile.Role.OWNER,
                EmployeeProfile.Role.DIRECTOR,
            }
            if not can_see_all:
                if not profile or not profile.primary_branch_id:
                    queryset = queryset.none()
                else:
                    queryset = queryset.filter(branch_id=profile.primary_branch_id)
        return BranchProductPriceSerializer(queryset, many=True, context=self.context).data


class CustomerSerializer(serializers.ModelSerializer):
    order_count = serializers.IntegerField(read_only=True)
    average_check = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Customer
        fields = "__all__"


class ShiftSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    is_open = serializers.BooleanField(read_only=True)

    class Meta:
        model = Shift
        fields = "__all__"


class OrderItemModifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItemModifier
        fields = ["id", "modifier", "name", "price_delta"]
        read_only_fields = ["name", "price_delta"]


class OrderItemSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(
        source="product", queryset=Product.objects.filter(is_active=True), write_only=True
    )
    modifier_ids = serializers.PrimaryKeyRelatedField(
        queryset=Modifier.objects.filter(is_active=True), many=True, required=False, write_only=True
    )
    modifiers = OrderItemModifierSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_id",
            "product_name",
            "unit_price",
            "quantity",
            "comment",
            "modifier_ids",
            "modifiers",
            "total_price",
        ]
        read_only_fields = ["product", "product_name", "unit_price"]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = ["order"]


class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = "__all__"


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    payments = PaymentSerializer(many=True, required=False, read_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    paid_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = ["order_number", "kitchen_started_at", "ready_at"]

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        branch = validated_data["branch"]
        last_id = Order.objects.filter(branch=branch).count() + 1
        order = Order.objects.create(order_number=f"{branch.id}-{last_id:05d}", **validated_data)

        for item_data in items_data:
            modifiers = item_data.pop("modifier_ids", [])
            product = item_data["product"]
            price = (
                BranchProductPrice.objects.filter(branch=branch, product=product, is_available=True)
                .values_list("price", flat=True)
                .first()
            )
            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                unit_price=price if price is not None else product.base_price,
                quantity=item_data.get("quantity", 1),
                comment=item_data.get("comment", ""),
            )
            for modifier in modifiers:
                OrderItemModifier.objects.create(
                    order_item=order_item,
                    modifier=modifier,
                    name=modifier.name,
                    price_delta=modifier.price_delta,
                )

        return order


class InventoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryItem
        fields = "__all__"


class RecipeItemSerializer(serializers.ModelSerializer):
    inventory_item_name = serializers.CharField(source="inventory_item.name", read_only=True)

    class Meta:
        model = RecipeItem
        fields = "__all__"


class StockBalanceSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    item_name = serializers.CharField(source="inventory_item.name", read_only=True)
    is_low = serializers.SerializerMethodField()

    class Meta:
        model = StockBalance
        fields = "__all__"

    def get_is_low(self, obj: StockBalance) -> bool:
        return obj.quantity <= obj.inventory_item.low_stock_threshold


class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = "__all__"


class NotificationRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationRule
        fields = "__all__"


class KPIEmployeeSerializer(serializers.Serializer):
    employee_id = serializers.IntegerField()
    employee_name = serializers.CharField()
    sales = serializers.DecimalField(max_digits=12, decimal_places=2)
    orders = serializers.IntegerField()
    average_service_seconds = serializers.IntegerField(allow_null=True)


class DashboardSerializer(serializers.Serializer):
    revenue_today = serializers.DecimalField(max_digits=12, decimal_places=2)
    revenue_month = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_check = serializers.DecimalField(max_digits=10, decimal_places=2)
    orders_today = serializers.IntegerField()
    top_products = serializers.ListField()
    branch_load = serializers.ListField()


def money(value) -> Decimal:
    return value or Decimal("0.00")
