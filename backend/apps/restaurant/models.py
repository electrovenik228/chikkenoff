from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Branch(TimeStampedModel):
    name = models.CharField(max_length=160)
    city = models.CharField(max_length=80)
    address = models.CharField(max_length=255)
    timezone = models.CharField(max_length=64, default="Asia/Bishkek")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["city", "name"]

    def __str__(self) -> str:
        return f"{self.city} - {self.name}"


class EmployeeProfile(TimeStampedModel):
    class Role(models.TextChoices):
        OWNER = "owner", "Владелец"
        DIRECTOR = "director", "Директор"
        MANAGER = "manager", "Менеджер"
        SHIFT_LEAD = "shift_lead", "Старший смены"
        CASHIER = "cashier", "Кассир"
        COOK = "cook", "Повар"
        COURIER = "courier", "Курьер"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="employee_profile")
    role = models.CharField(max_length=32, choices=Role.choices)
    primary_branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name="employees")
    phone = models.CharField(max_length=32, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"


class ProductCategory(TimeStampedModel):
    name = models.CharField(max_length=120)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name_plural = "product categories"

    def __str__(self) -> str:
        return self.name


class Product(TimeStampedModel):
    sku = models.CharField(max_length=64, unique=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_favorite = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    prep_seconds = models.PositiveIntegerField(default=360)

    class Meta:
        ordering = ["category__sort_order", "name"]

    def __str__(self) -> str:
        return self.name


class Modifier(TimeStampedModel):
    name = models.CharField(max_length=120)
    price_delta = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class ProductModifier(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="available_modifiers")
    modifier = models.ForeignKey(Modifier, on_delete=models.CASCADE, related_name="products")
    is_default = models.BooleanField(default=False)

    class Meta:
        unique_together = ("product", "modifier")


class BranchProductPrice(TimeStampedModel):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="product_prices")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="branch_prices")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ("branch", "product")

    def __str__(self) -> str:
        return f"{self.branch}: {self.product} - {self.price}"


class Customer(TimeStampedModel):
    full_name = models.CharField(max_length=160)
    phone = models.CharField(max_length=32, unique=True)
    birth_date = models.DateField(null=True, blank=True)
    bonus_balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    class Segment(models.TextChoices):
        VIP = "vip", "VIP"
        NEW = "new", "Новые"
        LOST = "lost", "Потерянные"
        REGULAR = "regular", "Постоянные"

    segment = models.CharField(max_length=24, choices=Segment.choices, default=Segment.NEW)

    def __str__(self) -> str:
        return f"{self.full_name} ({self.phone})"


class Shift(TimeStampedModel):
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="shifts")
    opened_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="opened_shifts")
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="closed_shifts"
    )
    opened_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)
    opening_cash = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    closing_cash = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)

    @property
    def is_open(self) -> bool:
        return self.closed_at is None

    def __str__(self) -> str:
        return f"{self.branch} / {self.opened_at:%Y-%m-%d %H:%M}"


class Order(TimeStampedModel):
    class Status(models.TextChoices):
        NEW = "new", "Новый"
        COOKING = "cooking", "Готовится"
        READY = "ready", "Готов"
        HANDED_OFF = "handed_off", "Выдан"
        CANCELED = "canceled", "Отменен"

    class Source(models.TextChoices):
        POS = "pos", "POS"
        WEBSITE = "website", "Сайт"
        MOBILE = "mobile", "Мобильное приложение"
        TELEGRAM = "telegram", "Telegram"
        WHATSAPP = "whatsapp", "WhatsApp"

    class ServiceType(models.TextChoices):
        DINE_IN = "dine_in", "В зале"
        TAKEAWAY = "takeaway", "С собой"
        DELIVERY = "delivery", "Доставка"

    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="orders")
    shift = models.ForeignKey(Shift, on_delete=models.PROTECT, null=True, blank=True, related_name="orders")
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    order_number = models.CharField(max_length=32, db_index=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.NEW)
    source = models.CharField(max_length=24, choices=Source.choices, default=Source.POS)
    service_type = models.CharField(max_length=24, choices=ServiceType.choices, default=ServiceType.TAKEAWAY)
    comment = models.TextField(blank=True)
    canceled_reason = models.TextField(blank=True)
    kitchen_started_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["branch", "status"]),
            models.Index(fields=["created_at"]),
        ]

    @property
    def total_amount(self) -> Decimal:
        return sum((item.total_price for item in self.items.all()), Decimal("0.00"))

    @property
    def paid_amount(self) -> Decimal:
        return sum((payment.amount for payment in self.payments.all()), Decimal("0.00"))

    def __str__(self) -> str:
        return f"#{self.order_number} {self.branch}"


class OrderItem(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    product_name = models.CharField(max_length=160)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    comment = models.TextField(blank=True)

    @property
    def modifiers_amount(self) -> Decimal:
        return sum((modifier.price_delta for modifier in self.modifiers.all()), Decimal("0.00"))

    @property
    def total_price(self) -> Decimal:
        return (self.unit_price + self.modifiers_amount) * self.quantity

    def __str__(self) -> str:
        return f"{self.quantity} x {self.product_name}"


class OrderItemModifier(TimeStampedModel):
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name="modifiers")
    modifier = models.ForeignKey(Modifier, on_delete=models.PROTECT)
    name = models.CharField(max_length=120)
    price_delta = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))


class Payment(TimeStampedModel):
    class Method(models.TextChoices):
        CASH = "cash", "Наличные"
        CARD = "card", "Карта"
        QR = "qr", "QR"
        BONUS = "bonus", "Бонусы"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    method = models.CharField(max_length=24, choices=Method.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    external_id = models.CharField(max_length=128, blank=True)

    def __str__(self) -> str:
        return f"{self.get_method_display()} {self.amount}"


class Delivery(TimeStampedModel):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="delivery")
    courier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    address = models.CharField(max_length=255)
    status = models.CharField(max_length=32, default="created")
    eta_minutes = models.PositiveIntegerField(null=True, blank=True)


class InventoryItem(TimeStampedModel):
    class Kind(models.TextChoices):
        INGREDIENT = "ingredient", "Ингредиент"
        SEMI_FINISHED = "semi_finished", "Полуфабрикат"
        DRINK = "drink", "Напиток"

    name = models.CharField(max_length=160)
    kind = models.CharField(max_length=32, choices=Kind.choices)
    unit = models.CharField(max_length=24, default="pcs")
    low_stock_threshold = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal("0.000"))

    def __str__(self) -> str:
        return self.name


class RecipeItem(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="recipe_items")
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT, related_name="recipes")
    quantity = models.DecimalField(max_digits=10, decimal_places=3)

    class Meta:
        unique_together = ("product", "inventory_item")


class StockBalance(TimeStampedModel):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="stock_balances")
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name="balances")
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0.000"))

    class Meta:
        unique_together = ("branch", "inventory_item")


class StockMovement(TimeStampedModel):
    class Reason(models.TextChoices):
        SALE = "sale", "Продажа"
        PURCHASE = "purchase", "Поставка"
        WRITE_OFF = "write_off", "Списание"
        INVENTORY = "inventory", "Инвентаризация"
        TRANSFER = "transfer", "Перемещение"

    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="stock_movements")
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT)
    quantity_delta = models.DecimalField(max_digits=12, decimal_places=3)
    reason = models.CharField(max_length=32, choices=Reason.choices)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name="stock_movements")
    comment = models.TextField(blank=True)


class NotificationRule(TimeStampedModel):
    class Channel(models.TextChoices):
        TELEGRAM = "telegram", "Telegram"
        SMS = "sms", "SMS"
        EMAIL = "email", "Email"

    event = models.CharField(max_length=64)
    channel = models.CharField(max_length=24, choices=Channel.choices)
    recipient = models.CharField(max_length=160)
    is_active = models.BooleanField(default=True)


class AuditLog(TimeStampedModel):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=120)
    entity = models.CharField(max_length=120)
    entity_id = models.CharField(max_length=64, blank=True)
    before = models.JSONField(default=dict, blank=True)
    after = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
