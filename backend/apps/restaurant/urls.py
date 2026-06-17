from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    BranchProductPriceViewSet,
    BranchViewSet,
    CustomerViewSet,
    DashboardAPIView,
    EmployeeProfileViewSet,
    InventoryItemViewSet,
    ModifierViewSet,
    NotificationRuleViewSet,
    OrderViewSet,
    PaymentViewSet,
    ProductCategoryViewSet,
    ProductViewSet,
    RecipeItemViewSet,
    ShiftViewSet,
    StockBalanceViewSet,
    StockMovementViewSet,
)

router = DefaultRouter()
router.register("branches", BranchViewSet)
router.register("employees", EmployeeProfileViewSet)
router.register("categories", ProductCategoryViewSet)
router.register("products", ProductViewSet)
router.register("modifiers", ModifierViewSet)
router.register("branch-prices", BranchProductPriceViewSet)
router.register("customers", CustomerViewSet, basename="customers")
router.register("shifts", ShiftViewSet)
router.register("orders", OrderViewSet)
router.register("payments", PaymentViewSet)
router.register("inventory-items", InventoryItemViewSet)
router.register("recipe-items", RecipeItemViewSet)
router.register("stock-balances", StockBalanceViewSet)
router.register("stock-movements", StockMovementViewSet)
router.register("notification-rules", NotificationRuleViewSet)

urlpatterns = [
    path("dashboard/", DashboardAPIView.as_view(), name="dashboard"),
    *router.urls,
]
