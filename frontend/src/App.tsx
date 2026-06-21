import {
  AccessTime,
  Add,
  CreditCard,
  Delete,
  Inventory2,
  LocalPrintshop,
  PeopleAlt,
  Payments,
  QrCode2,
  ReceiptLong,
  Remove,
  Search,
  SoupKitchen,
  Store,
  TrendingUp
} from "@mui/icons-material";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  IconButton,
  InputAdornment,
  LinearProgress,
  Snackbar,
  Stack,
  Tab,
  Tabs,
  TextField,
  Tooltip,
  Typography
} from "@mui/material";
import { useMemo, useState } from "react";

import {
  BranchName,
  CartItem,
  Category,
  KitchenOrder,
  branches,
  branchStats,
  categories,
  customers,
  kitchenOrders,
  modifiers,
  products,
  stockAlerts
} from "./data/mock";

type Screen = "pos" | "kds" | "dashboard" | "branches" | "crm" | "stock";
type PaymentMethod = "cash" | "card" | "qr" | "split";

const currency = new Intl.NumberFormat("ru-KG", { style: "currency", currency: "KGS", maximumFractionDigits: 0 });

function App() {
  const [screen, setScreen] = useState<Screen>("pos");
  const [category, setCategory] = useState<Category | "all" | "favorite">("favorite");
  const [query, setQuery] = useState("");
  const [cart, setCart] = useState<CartItem[]>([]);
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>("card");
  const [orders, setOrders] = useState<KitchenOrder[]>(kitchenOrders);
  const [nextOrderNumber, setNextOrderNumber] = useState(43);
  const [notice, setNotice] = useState("");
  const [activeBranchName, setActiveBranchName] = useState<BranchName>("Бишкек Центр");

  const activeBranch = branches.find((branch) => branch.name === activeBranchName) ?? branches[0];
  const activeBranchStats = branchStats.find((branch) => branch.name === activeBranchName) ?? branchStats[0];
  const visibleOrders = orders.filter((order) => order.branch === activeBranchName);
  const visibleCustomers = customers.filter((customer) => customer.branch === activeBranchName);
  const visibleStockAlerts = stockAlerts.filter((stock) => stock.branch === activeBranchName);

  const filteredProducts = useMemo(() => {
    return products.filter((product) => {
      const matchesCategory =
        category === "all" || (category === "favorite" ? product.favorite : product.category === category);
      const matchesQuery = product.name.toLowerCase().includes(query.toLowerCase());
      return matchesCategory && matchesQuery;
    });
  }, [category, query]);

  const subtotal = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
  const totalQuantity = cart.reduce((sum, item) => sum + item.quantity, 0);

  const addProduct = (productId: number) => {
    const product = products.find((item) => item.id === productId);
    if (!product) return;
    const branchPrice = product.branchPrices?.[activeBranchName] ?? product.price;
    setCart((current) => {
      const existing = current.find((item) => item.id === product.id && item.modifiers.length === 0);
      if (existing) {
        return current.map((item) => (item === existing ? { ...item, quantity: item.quantity + 1 } : item));
      }
      return [...current, { ...product, price: branchPrice, quantity: 1, modifiers: [] }];
    });
  };

  const changeBranch = (branchName: BranchName) => {
    setActiveBranchName(branchName);
    setCart([]);
    setNotice(`Открыт филиал: ${branchName}`);
  };

  const updateQuantity = (productId: number, delta: number) => {
    setCart((current) =>
      current
        .map((item) => (item.id === productId ? { ...item, quantity: Math.max(0, item.quantity + delta) } : item))
        .filter((item) => item.quantity > 0)
    );
  };

  const toggleModifier = (productId: number, modifier: string) => {
    setCart((current) =>
      current.map((item) => {
        if (item.id !== productId) return item;
        const hasModifier = item.modifiers.includes(modifier);
        return {
          ...item,
          modifiers: hasModifier ? item.modifiers.filter((value) => value !== modifier) : [...item.modifiers, modifier]
        };
      })
    );
  };

  const payOrder = () => {
    if (!cart.length) return;
    const orderId = `${activeBranch.code}-${String(nextOrderNumber).padStart(5, "0")}`;
    const kitchenOrder: KitchenOrder = {
      id: orderId,
      branch: activeBranchName,
      status: "new",
      minutes: 0,
      source: "POS",
      items: cart.map((item) => {
        const modifiersText = item.modifiers.length ? ` (${item.modifiers.join(", ")})` : "";
        return `${item.name} x${item.quantity}${modifiersText}`;
      })
    };
    setOrders((current) => [kitchenOrder, ...current]);
    setNextOrderNumber((current) => current + 1);
    setCart([]);
    setNotice(`Заказ #${orderId} оплачен и отправлен на кухню ${activeBranchName}`);
    setScreen("kds");
  };

  const updateKitchenOrderStatus = (orderId: string, status: KitchenOrder["status"]) => {
    setOrders((current) => current.map((order) => (order.id === orderId ? { ...order, status } : order)));
    setNotice(`Заказ #${orderId}: ${status === "cooking" ? "готовится" : status === "ready" ? "готов" : "новый"}`);
  };

  return (
    <Box className="app-shell">
      <Box className="topbar">
        <Stack direction="row" alignItems="center" spacing={1.5}>
          <Box className="brand-mark">CH</Box>
          <Box>
            <Typography variant="h6">Chikkenoff Cloud POS</Typography>
            <Typography variant="body2" color="text.secondary">
              {activeBranch.name} · {activeBranch.shift}
            </Typography>
          </Box>
        </Stack>
        <Box>
          <Tabs value={screen} onChange={(_, value) => setScreen(value)} variant="scrollable" allowScrollButtonsMobile>
            <Tab icon={<ReceiptLong />} iconPosition="start" label="POS" value="pos" />
            <Tab icon={<SoupKitchen />} iconPosition="start" label="KDS" value="kds" />
            <Tab icon={<TrendingUp />} iconPosition="start" label="Аналитика" value="dashboard" />
            <Tab icon={<Store />} iconPosition="start" label="Филиал" value="branches" />
            <Tab icon={<PeopleAlt />} iconPosition="start" label="CRM" value="crm" />
            <Tab icon={<Inventory2 />} iconPosition="start" label="Склад" value="stock" />
          </Tabs>
          <Stack direction="row" spacing={1} className="branch-switcher">
            {branches.map((branch) => (
              <Button
                key={branch.name}
                size="small"
                variant={activeBranchName === branch.name ? "contained" : "outlined"}
                onClick={() => changeBranch(branch.name)}
              >
                {branch.name}
              </Button>
            ))}
          </Stack>
        </Box>
      </Box>

      {screen === "pos" && (
        <Box className="pos-layout">
          <Box className="catalog-panel">
            <Stack direction={{ xs: "column", md: "row" }} spacing={1.5} alignItems={{ md: "center" }}>
              <TextField
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Поиск товара"
                size="small"
                fullWidth
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search />
                    </InputAdornment>
                  )
                }}
              />
              <Stack direction="row" spacing={1} className="quick-actions">
                <Button variant="outlined" onClick={() => addProduct(1)}>
                  Чизбургер
                </Button>
                <Button variant="outlined" onClick={() => addProduct(4)}>
                  Кола
                </Button>
                <Button variant="outlined" onClick={() => addProduct(8)}>
                  Фри
                </Button>
              </Stack>
            </Stack>

            <Stack direction="row" spacing={1} className="category-row">
              {categories.map((item) => (
                <Button
                  key={item.id}
                  variant={category === item.id ? "contained" : "outlined"}
                  onClick={() => setCategory(item.id)}
                >
                  {item.label}
                </Button>
              ))}
            </Stack>

            <Box className="product-grid">
              {filteredProducts.map((product) => (
                <button key={product.id} className="product-tile" onClick={() => addProduct(product.id)}>
                  <span className="tile-code">{product.name.slice(0, 2).toUpperCase()}</span>
                  <span className="tile-name">{product.name}</span>
                  <span className="tile-price">{currency.format(product.branchPrices?.[activeBranchName] ?? product.price)}</span>
                </button>
              ))}
            </Box>
          </Box>

          <Box className="order-panel">
            <Stack direction="row" justifyContent="space-between" alignItems="center">
              <Box>
                <Typography variant="h6">Заказ</Typography>
                <Typography variant="body2" color="text.secondary">
                  {totalQuantity} позиций · #{cart.length ? `${activeBranch.code}-${String(nextOrderNumber).padStart(5, "0")}` : "новый"}
                </Typography>
              </Box>
              <Tooltip title="Очистить заказ">
                <span>
                  <IconButton disabled={!cart.length} onClick={() => setCart([])} color="error">
                    <Delete />
                  </IconButton>
                </span>
              </Tooltip>
            </Stack>

            <Box className="cart-list">
              {cart.length === 0 && <Typography className="empty-state">Добавьте товар быстрыми кнопками</Typography>}
              {cart.map((item) => (
                <Card key={item.id} className="cart-item">
                  <CardContent>
                    <Stack spacing={1}>
                      <Stack direction="row" justifyContent="space-between" alignItems="center">
                        <Box>
                          <Typography fontWeight={800}>{item.name}</Typography>
                          <Typography variant="body2" color="text.secondary">
                            {currency.format(item.price)} · {item.modifiers.join(", ") || "без модификаторов"}
                          </Typography>
                        </Box>
                        <Stack direction="row" alignItems="center" spacing={0.5}>
                          <Tooltip title="Уменьшить">
                            <IconButton onClick={() => updateQuantity(item.id, -1)}>
                              <Remove />
                            </IconButton>
                          </Tooltip>
                          <Typography className="quantity">{item.quantity}</Typography>
                          <Tooltip title="Увеличить">
                            <IconButton onClick={() => updateQuantity(item.id, 1)}>
                              <Add />
                            </IconButton>
                          </Tooltip>
                        </Stack>
                      </Stack>
                      <Stack direction="row" spacing={0.75} flexWrap="wrap" useFlexGap>
                        {modifiers.map((modifier) => (
                          <Chip
                            key={modifier}
                            label={modifier}
                            color={item.modifiers.includes(modifier) ? "primary" : "default"}
                            variant={item.modifiers.includes(modifier) ? "filled" : "outlined"}
                            onClick={() => toggleModifier(item.id, modifier)}
                          />
                        ))}
                      </Stack>
                    </Stack>
                  </CardContent>
                </Card>
              ))}
            </Box>

            <Divider />
            <Stack spacing={1.25}>
              <Stack direction="row" justifyContent="space-between">
                <Typography color="text.secondary">Итого</Typography>
                <Typography variant="h5">{currency.format(subtotal)}</Typography>
              </Stack>
              <Stack direction="row" spacing={1}>
                <Tooltip title="Наличные">
                  <IconButton
                    color={paymentMethod === "cash" ? "primary" : "default"}
                    onClick={() => setPaymentMethod("cash")}
                  >
                    <Payments />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Карта">
                  <IconButton
                    color={paymentMethod === "card" ? "primary" : "default"}
                    onClick={() => setPaymentMethod("card")}
                  >
                    <CreditCard />
                  </IconButton>
                </Tooltip>
                <Tooltip title="QR">
                  <IconButton color={paymentMethod === "qr" ? "primary" : "default"} onClick={() => setPaymentMethod("qr")}>
                    <QrCode2 />
                  </IconButton>
                </Tooltip>
                <Button
                  variant={paymentMethod === "split" ? "contained" : "outlined"}
                  onClick={() => setPaymentMethod("split")}
                >
                  Смешанная
                </Button>
              </Stack>
              <Stack direction="row" spacing={1}>
                <Button variant="contained" fullWidth disabled={!cart.length} onClick={payOrder}>
                  Оплатить
                </Button>
                <Tooltip title="Кухонный чек">
                  <span>
                    <IconButton disabled={!cart.length} onClick={() => setNotice("Кухонный чек отправлен на печать")}>
                      <LocalPrintshop />
                    </IconButton>
                  </span>
                </Tooltip>
              </Stack>
            </Stack>
          </Box>
        </Box>
      )}

      {screen === "kds" && <KdsScreen branchName={activeBranchName} orders={visibleOrders} onStatusChange={updateKitchenOrderStatus} />}
      {screen === "dashboard" && <DashboardScreen branchName={activeBranchName} branchStats={activeBranchStats} orders={visibleOrders} />}
      {screen === "branches" && <BranchesScreen branchName={activeBranchName} branchStats={activeBranchStats} />}
      {screen === "crm" && <CrmScreen customers={visibleCustomers} />}
      {screen === "stock" && <StockScreen stockAlerts={visibleStockAlerts} />}
      <Snackbar open={Boolean(notice)} autoHideDuration={2600} onClose={() => setNotice("")}>
        <Alert severity="success" variant="filled" onClose={() => setNotice("")}>
          {notice}
        </Alert>
      </Snackbar>
    </Box>
  );
}

function KdsScreen({
  branchName,
  orders,
  onStatusChange
}: {
  branchName: BranchName;
  orders: KitchenOrder[];
  onStatusChange: (orderId: string, status: KitchenOrder["status"]) => void;
}) {
  return (
    <Box className="work-area">
      {orders.length === 0 && <Typography className="empty-state">В филиале {branchName} нет активных заказов кухни</Typography>}
      <Box className="kds-grid">
        {orders.map((order) => {
          const tone = order.minutes >= 12 ? "danger" : order.minutes >= 8 ? "warning" : "success";
          return (
            <Card key={order.id} className={`kds-card ${tone}`}>
              <CardContent>
                <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                  <Box>
                    <Typography variant="h6">#{order.id}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {order.branch} · {order.source}
                    </Typography>
                  </Box>
                  <Stack alignItems="flex-end" spacing={1}>
                    <Chip
                      icon={<AccessTime />}
                      label={`${order.minutes} мин`}
                      color={tone === "danger" ? "error" : tone === "warning" ? "warning" : "success"}
                    />
                    <Chip label={statusLabel(order.status)} variant="outlined" />
                  </Stack>
                </Stack>
                <Divider />
                <Stack spacing={1}>
                  {order.items.map((item) => (
                    <Typography key={item} fontWeight={700}>
                      {item}
                    </Typography>
                  ))}
                </Stack>
                <Stack direction="row" spacing={1}>
                  <Button
                    variant={order.status === "cooking" ? "contained" : "outlined"}
                    fullWidth
                    disabled={order.status === "ready"}
                    onClick={() => onStatusChange(order.id, "cooking")}
                  >
                    Готовится
                  </Button>
                  <Button
                    variant={order.status === "ready" ? "contained" : "outlined"}
                    color="success"
                    fullWidth
                    disabled={order.status === "ready"}
                    onClick={() => onStatusChange(order.id, "ready")}
                  >
                    Готов
                  </Button>
                </Stack>
              </CardContent>
            </Card>
          );
        })}
      </Box>
    </Box>
  );
}

function statusLabel(status: KitchenOrder["status"]) {
  if (status === "new") return "Новый";
  if (status === "cooking") return "Готовится";
  return "Готов";
}

function DashboardScreen({
  branchName,
  branchStats,
  orders
}: {
  branchName: BranchName;
  branchStats: { name: BranchName; revenue: number; profit: number; avgCheck: number; orders: number };
  orders: KitchenOrder[];
}) {
  return (
    <Box className="work-area">
      <Box className="metric-grid">
        <Metric title="Филиал" value={branchName} />
        <Metric title="Выручка за месяц" value={currency.format(branchStats.revenue)} />
        <Metric title="Средний чек" value={currency.format(branchStats.avgCheck)} />
        <Metric title="Активные заказы" value={String(orders.length)} />
      </Box>
      <Box className="split-grid">
        <Card>
          <CardContent>
            <Typography variant="h6">Топ товаров</Typography>
            {products.slice(0, 5).map((product, index) => (
              <Box key={product.id} className="rank-row">
                <Typography>{index + 1}. {product.name}</Typography>
                <LinearProgress variant="determinate" value={90 - index * 12} />
              </Box>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography variant="h6">AI Аналитик</Typography>
            <Stack spacing={1.25} className="ai-list">
              <Typography>{branchName}: активных заказов кухни сейчас {orders.length}.</Typography>
              <Typography>Кола и Фри чаще всего покупаются вместе с Чизбургером. Комбо-кнопка сократит клики кассира.</Typography>
              <Typography>Прогноз склада считается только по выбранному филиалу.</Typography>
            </Stack>
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
}

function BranchesScreen({
  branchName,
  branchStats
}: {
  branchName: BranchName;
  branchStats: { name: BranchName; revenue: number; profit: number; avgCheck: number; orders: number };
}) {
  return (
    <Box className="work-area">
      <Box className="table-card">
        <Box className="table-header branch-table">
          <span>Филиал</span>
          <span>Выручка</span>
          <span>Прибыль</span>
          <span>Средний чек</span>
          <span>Заказы</span>
        </Box>
        <Box className="table-row branch-table">
          <strong>{branchName}</strong>
          <span>{currency.format(branchStats.revenue)}</span>
          <span>{currency.format(branchStats.profit)}</span>
          <span>{currency.format(branchStats.avgCheck)}</span>
          <span>{branchStats.orders}</span>
        </Box>
      </Box>
    </Box>
  );
}

function CrmScreen({
  customers
}: {
  customers: { name: string; phone: string; segment: string; orders: number; avg: number; favorite: string }[];
}) {
  return (
    <Box className="work-area">
      <Box className="table-card">
        <Box className="table-header crm-table">
          <span>Клиент</span>
          <span>Телефон</span>
          <span>Сегмент</span>
          <span>Заказы</span>
          <span>Средний чек</span>
          <span>Любимое</span>
        </Box>
        {customers.map((customer) => (
          <Box key={customer.phone} className="table-row crm-table">
            <strong>{customer.name}</strong>
            <span>{customer.phone}</span>
            <Chip label={customer.segment} size="small" />
            <span>{customer.orders}</span>
            <span>{currency.format(customer.avg)}</span>
            <span>{customer.favorite}</span>
          </Box>
        ))}
        {customers.length === 0 && <Typography className="empty-state">В этом филиале пока нет клиентов</Typography>}
      </Box>
    </Box>
  );
}

function StockScreen({
  stockAlerts
}: {
  stockAlerts: { item: string; branch: BranchName; balance: string; threshold: string }[];
}) {
  return (
    <Box className="work-area">
      <Box className="table-card">
        <Box className="table-header stock-table">
          <span>Позиция</span>
          <span>Филиал</span>
          <span>Остаток</span>
          <span>Порог</span>
          <span>Статус</span>
        </Box>
        {stockAlerts.map((stock) => (
          <Box key={`${stock.branch}-${stock.item}`} className="table-row stock-table">
            <strong>{stock.item}</strong>
            <span>{stock.branch}</span>
            <span>{stock.balance}</span>
            <span>{stock.threshold}</span>
            <Chip label="низкий остаток" color="warning" size="small" />
          </Box>
        ))}
        {stockAlerts.length === 0 && <Typography className="empty-state">В этом филиале нет критичных остатков</Typography>}
      </Box>
    </Box>
  );
}

function Metric({ title, value }: { title: string; value: string }) {
  return (
    <Card>
      <CardContent>
        <Typography variant="body2" color="text.secondary">
          {title}
        </Typography>
        <Typography variant="h5">{value}</Typography>
      </CardContent>
    </Card>
  );
}

export default App;
