from datetime import timedelta

from django.db.models import Avg, Count, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import decorators, response, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
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


HQ_ROLES = {EmployeeProfile.Role.OWNER, EmployeeProfile.Role.DIRECTOR}


class BranchAccessMixin:
    branch_lookup = None
    branch_write_field = "branch"
    global_only = False

    def employee_profile(self):
        user = self.request.user
        if not user.is_authenticated:
            return None
        return getattr(user, "employee_profile", None)

    def can_access_all_branches(self) -> bool:
        user = self.request.user
        profile = self.employee_profile()
        return bool(
            user.is_authenticated
            and (user.is_superuser or (profile and profile.is_active and profile.role in HQ_ROLES))
        )

    def user_branch_id(self):
        profile = self.employee_profile()
        if not profile or not profile.is_active or not profile.primary_branch_id:
            return None
        return profile.primary_branch_id

    def user_branch(self):
        profile = self.employee_profile()
        if not profile or not profile.is_active:
            return None
        return profile.primary_branch

    def scope_queryset(self, queryset, branch_lookup=None):
        if self.can_access_all_branches():
            return queryset
        if self.global_only:
            return queryset.none()
        lookup = branch_lookup if branch_lookup is not None else self.branch_lookup
        branch_id = self.user_branch_id()
        if not lookup or not branch_id:
            return queryset.none()
        return queryset.filter(**{lookup: branch_id}).distinct()

    def save_with_branch_scope(self, serializer):
        if self.can_access_all_branches():
            serializer.save()
            return

        branch = self.user_branch()
        if not branch:
            raise PermissionDenied("Пользователь не привязан к активному филиалу.")

        if not self.branch_write_field:
            raise PermissionDenied("Недостаточно прав для изменения этого ресурса.")

        serializer.save(**{self.branch_write_field: branch})


class BaseModelViewSet(BranchAccessMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.scope_queryset(super().get_queryset())

    def perform_create(self, serializer):
        self.save_with_branch_scope(serializer)

    def perform_update(self, serializer):
        self.save_with_branch_scope(serializer)


class BranchViewSet(BaseModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    branch_lookup = "id"
    branch_write_field = None


class EmployeeProfileViewSet(BaseModelViewSet):
    queryset = EmployeeProfile.objects.select_related("user", "primary_branch")
    serializer_class = EmployeeProfileSerializer
    branch_lookup = "primary_branch_id"
    branch_write_field = "primary_branch"


class ProductCategoryViewSet(BaseModelViewSet):
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    branch_lookup = "products__branch_prices__branch_id"
    branch_write_field = None


class ProductViewSet(BaseModelViewSet):
    queryset = Product.objects.select_related("category").prefetch_related("available_modifiers__modifier", "branch_prices")
    serializer_class = ProductSerializer
    branch_lookup = "branch_prices__branch_id"
    branch_write_field = None

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
    branch_lookup = "products__product__branch_prices__branch_id"
    branch_write_field = None


class BranchProductPriceViewSet(BaseModelViewSet):
    queryset = BranchProductPrice.objects.select_related("branch", "product")
    serializer_class = BranchProductPriceSerializer
    branch_lookup = "branch_id"
    branch_write_field = "branch"


class CustomerViewSet(BaseModelViewSet):
    serializer_class = CustomerSerializer
    branch_lookup = "orders__branch_id"
    branch_write_field = None

    def get_queryset(self):
        line_total = ExpressionWrapper(
            (F("orders__items__unit_price") * F("orders__items__quantity")),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
        queryset = Customer.objects.all()
        if not self.can_access_all_branches():
            branch_id = self.user_branch_id()
            if not branch_id:
                return Customer.objects.none()
            queryset = queryset.filter(orders__branch_id=branch_id)
        return queryset.distinct().annotate(
            order_count=Count("orders", distinct=True),
            average_check=Coalesce(Avg(line_total), 0, output_field=DecimalField(max_digits=10, decimal_places=2)),
        )


class ShiftViewSet(BaseModelViewSet):
    queryset = Shift.objects.select_related("branch", "opened_by", "closed_by")
    serializer_class = ShiftSerializer
    branch_lookup = "branch_id"
    branch_write_field = "branch"

    def perform_create(self, serializer):
        if self.can_access_all_branches():
            serializer.save(opened_by=self.request.user)
            return
        branch = self.user_branch()
        if not branch:
            raise PermissionDenied("Пользователь не привязан к активному филиалу.")
        serializer.save(branch=branch, opened_by=self.request.user)

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
    branch_lookup = "branch_id"
    branch_write_field = "branch"

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

    def perform_create(self, serializer):
        if self.can_access_all_branches():
            serializer.save(cashier=self.request.user)
            return
        branch = self.user_branch()
        if not branch:
            raise PermissionDenied("Пользователь не привязан к активному филиалу.")
        serializer.save(branch=branch, cashier=self.request.user)

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
    branch_lookup = "order__branch_id"
    branch_write_field = None


class InventoryItemViewSet(BaseModelViewSet):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    branch_lookup = "balances__branch_id"
    branch_write_field = None


class RecipeItemViewSet(BaseModelViewSet):
    queryset = RecipeItem.objects.select_related("product", "inventory_item")
    serializer_class = RecipeItemSerializer
    branch_lookup = "product__branch_prices__branch_id"
    branch_write_field = None


class StockBalanceViewSet(BaseModelViewSet):
    queryset = StockBalance.objects.select_related("branch", "inventory_item")
    serializer_class = StockBalanceSerializer
    branch_lookup = "branch_id"
    branch_write_field = "branch"

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
    branch_lookup = "branch_id"
    branch_write_field = "branch"


class NotificationRuleViewSet(BaseModelViewSet):
    queryset = NotificationRule.objects.all()
    serializer_class = NotificationRuleSerializer
    global_only = True
    branch_write_field = None


class DashboardAPIView(BranchAccessMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        paid_orders = self.scope_queryset(Order.objects.exclude(status=Order.Status.CANCELED), "branch_id")
        scoped_payments = self.scope_queryset(Payment.objects.all(), "order__branch_id")

        revenue_today = money(scoped_payments.filter(order__created_at__gte=today_start).aggregate(total=Sum("amount"))["total"])
        revenue_month = money(scoped_payments.filter(order__created_at__gte=month_start).aggregate(total=Sum("amount"))["total"])
        orders_today = paid_orders.filter(created_at__gte=today_start).count()
        average_check = revenue_today / orders_today if orders_today else 0

        top_products = (
            self.scope_queryset(OrderItem.objects.all(), "order__branch_id")
            .filter(order__created_at__gte=month_start, order__status__in=[
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
