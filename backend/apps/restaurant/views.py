from datetime import timedelta

from django.db.models import Avg, Count, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import decorators, response, status, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.views import APIView

from .models import (
    Branch,
    BranchProductPrice,
    Customer,
    EmployeeProfile,
    InventoryItem,
    Modifier,
    NotificationRule,
    Order,
    OrderItem,
    Payment,
    Product,
    ProductCategory,
    RecipeItem,
    Shift,
    StockBalance,
    StockMovement,
)
from .serializers import (
    BranchProductPriceSerializer,
    BranchSerializer,
    CustomerSerializer,
    EmployeeProfileSerializer,
    InventoryItemSerializer,
    ModifierSerializer,
    NotificationRuleSerializer,
    OrderSerializer,
    PaymentSerializer,
    ProductCategorySerializer,
    ProductSerializer,
    RecipeItemSerializer,
    ShiftSerializer,
    StockBalanceSerializer,
    StockMovementSerializer,
    money,
)


class BaseModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]


class BranchViewSet(BaseModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer


class EmployeeProfileViewSet(BaseModelViewSet):
    queryset = EmployeeProfile.objects.select_related("user", "primary_branch")
    serializer_class = EmployeeProfileSerializer


class ProductCategoryViewSet(BaseModelViewSet):
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer


class ProductViewSet(BaseModelViewSet):
    queryset = Product.objects.select_related("category").prefetch_related("available_modifiers__modifier", "branch_prices")
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get("search")
        category = self.request.query_params.get("category")
        favorites = self.request.query_params.get("favorites")
        if search:
            queryset = queryset.filter(name__icontains=search)
        if category:
            queryset = queryset.filter(category_id=category)
        if favorites in {"1", "true", "True"}:
            queryset = queryset.filter(is_favorite=True)
        return queryset


class ModifierViewSet(BaseModelViewSet):
    queryset = Modifier.objects.all()
    serializer_class = ModifierSerializer


class BranchProductPriceViewSet(BaseModelViewSet):
    queryset = BranchProductPrice.objects.select_related("branch", "product")
    serializer_class = BranchProductPriceSerializer


class CustomerViewSet(BaseModelViewSet):
    serializer_class = CustomerSerializer

    def get_queryset(self):
        line_total = ExpressionWrapper(
            (F("orders__items__unit_price") * F("orders__items__quantity")),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
        return Customer.objects.annotate(
            order_count=Count("orders", distinct=True),
            average_check=Coalesce(Avg(line_total), 0, output_field=DecimalField(max_digits=10, decimal_places=2)),
        )


class ShiftViewSet(BaseModelViewSet):
    queryset = Shift.objects.select_related("branch", "opened_by", "closed_by")
    serializer_class = ShiftSerializer

    @decorators.action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        shift = self.get_object()
        shift.closed_by = request.user if request.user.is_authenticated else shift.opened_by
        shift.closed_at = timezone.now()
        shift.closing_cash = request.data.get("closing_cash", shift.closing_cash)
        shift.notes = request.data.get("notes", shift.notes)
        shift.save(update_fields=["closed_by", "closed_at", "closing_cash", "notes", "updated_at"])
        return response.Response(self.get_serializer(shift).data)


class OrderViewSet(BaseModelViewSet):
    queryset = (
        Order.objects.select_related("branch", "shift", "cashier", "customer")
        .prefetch_related("items__modifiers", "payments")
        .all()
    )
    serializer_class = OrderSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        branch = self.request.query_params.get("branch")
        status_value = self.request.query_params.get("status")
        source = self.request.query_params.get("source")
        if branch:
            queryset = queryset.filter(branch_id=branch)
        if status_value:
            queryset = queryset.filter(status=status_value)
        if source:
            queryset = queryset.filter(source=source)
        return queryset

    @decorators.action(detail=False, methods=["get"])
    def kds(self, request):
        queryset = self.get_queryset().filter(status__in=[Order.Status.NEW, Order.Status.COOKING, Order.Status.READY])
        return response.Response(self.get_serializer(queryset, many=True).data)

    @decorators.action(detail=True, methods=["post"])
    def transition(self, request, pk=None):
        order = self.get_object()
        next_status = request.data.get("status")
        valid = {choice[0] for choice in Order.Status.choices}
        if next_status not in valid:
            return response.Response({"detail": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)
        order.status = next_status
        if next_status == Order.Status.COOKING and not order.kitchen_started_at:
            order.kitchen_started_at = timezone.now()
        if next_status == Order.Status.READY and not order.ready_at:
            order.ready_at = timezone.now()
        order.save(update_fields=["status", "kitchen_started_at", "ready_at", "updated_at"])
        return response.Response(self.get_serializer(order).data)

    @decorators.action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        order = self.get_object()
        serializer = PaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = serializer.save(order=order)
        return response.Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class PaymentViewSet(BaseModelViewSet):
    queryset = Payment.objects.select_related("order")
    serializer_class = PaymentSerializer


class InventoryItemViewSet(BaseModelViewSet):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer


class RecipeItemViewSet(BaseModelViewSet):
    queryset = RecipeItem.objects.select_related("product", "inventory_item")
    serializer_class = RecipeItemSerializer


class StockBalanceViewSet(BaseModelViewSet):
    queryset = StockBalance.objects.select_related("branch", "inventory_item")
    serializer_class = StockBalanceSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        branch = self.request.query_params.get("branch")
        low = self.request.query_params.get("low")
        if branch:
            queryset = queryset.filter(branch_id=branch)
        if low in {"1", "true", "True"}:
            queryset = queryset.filter(quantity__lte=F("inventory_item__low_stock_threshold"))
        return queryset


class StockMovementViewSet(BaseModelViewSet):
    queryset = StockMovement.objects.select_related("branch", "inventory_item", "order")
    serializer_class = StockMovementSerializer


class NotificationRuleViewSet(BaseModelViewSet):
    queryset = NotificationRule.objects.all()
    serializer_class = NotificationRuleSerializer


class DashboardAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        paid_orders = Order.objects.exclude(status=Order.Status.CANCELED)

        revenue_today = money(Payment.objects.filter(order__created_at__gte=today_start).aggregate(total=Sum("amount"))["total"])
        revenue_month = money(Payment.objects.filter(order__created_at__gte=month_start).aggregate(total=Sum("amount"))["total"])
        orders_today = paid_orders.filter(created_at__gte=today_start).count()
        average_check = revenue_today / orders_today if orders_today else 0

        top_products = (
            OrderItem.objects.filter(order__created_at__gte=month_start, order__status__in=[
                Order.Status.NEW,
                Order.Status.COOKING,
                Order.Status.READY,
                Order.Status.HANDED_OFF,
            ])
            .values("product_id", "product_name")
            .annotate(quantity=Sum("quantity"))
            .order_by("-quantity")[:5]
        )

        branch_load = (
            paid_orders.filter(created_at__gte=today_start)
            .values("branch_id", "branch__name")
            .annotate(orders=Count("id"))
            .order_by("-orders")
        )

        delayed_from = now - timedelta(minutes=12)
        delayed_orders = paid_orders.filter(status=Order.Status.COOKING, kitchen_started_at__lt=delayed_from).count()

        return response.Response(
            {
                "revenue_today": revenue_today,
                "revenue_month": revenue_month,
                "average_check": average_check,
                "orders_today": orders_today,
                "top_products": list(top_products),
                "branch_load": list(branch_load),
                "delayed_orders": delayed_orders,
            }
        )
