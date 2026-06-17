export type Category = "burgers" | "drinks" | "sets" | "sides";

export type Product = {
  id: number;
  category: Category;
  name: string;
  price: number;
  favorite?: boolean;
  prepSeconds: number;
};

export type CartItem = Product & {
  quantity: number;
  modifiers: string[];
  comment?: string;
};

export type KitchenOrder = {
  id: string;
  branch: string;
  status: "new" | "cooking" | "ready";
  minutes: number;
  source: "POS" | "Telegram" | "Site";
  items: string[];
};

export const categories: { id: Category | "all" | "favorite"; label: string }[] = [
  { id: "all", label: "Все" },
  { id: "favorite", label: "Избранное" },
  { id: "burgers", label: "Бургеры" },
  { id: "drinks", label: "Напитки" },
  { id: "sets", label: "Комбо" },
  { id: "sides", label: "Гарниры" }
];

export const products: Product[] = [
  { id: 1, category: "burgers", name: "Чизбургер", price: 220, favorite: true, prepSeconds: 360 },
  { id: 2, category: "burgers", name: "Гамбургер", price: 190, favorite: true, prepSeconds: 300 },
  { id: 3, category: "burgers", name: "Биг Бургер", price: 340, favorite: true, prepSeconds: 420 },
  { id: 4, category: "drinks", name: "Кола", price: 80, favorite: true, prepSeconds: 30 },
  { id: 5, category: "drinks", name: "Фанта", price: 80, prepSeconds: 30 },
  { id: 6, category: "drinks", name: "Сок", price: 95, prepSeconds: 30 },
  { id: 7, category: "sets", name: "Комбо Бургер", price: 390, favorite: true, prepSeconds: 480 },
  { id: 8, category: "sides", name: "Картофель фри", price: 120, favorite: true, prepSeconds: 240 },
  { id: 9, category: "sides", name: "Наггетсы", price: 170, prepSeconds: 300 }
];

export const modifiers = ["без лука", "двойной сыр", "extra соус", "острый соус"];

export const kitchenOrders: KitchenOrder[] = [
  { id: "1-00042", branch: "Бишкек Центр", status: "new", minutes: 2, source: "POS", items: ["Чизбургер x2", "Кола x2"] },
  { id: "1-00041", branch: "Бишкек Центр", status: "cooking", minutes: 9, source: "Telegram", items: ["Биг Бургер", "Фри"] },
  { id: "2-00018", branch: "Бишкек Юг", status: "cooking", minutes: 15, source: "Site", items: ["Комбо Бургер x3"] },
  { id: "1-00040", branch: "Бишкек Центр", status: "ready", minutes: 6, source: "POS", items: ["Гамбургер", "Сок"] }
];

export const branchStats = [
  { name: "Бишкек Центр", revenue: 128400, profit: 37600, avgCheck: 328, orders: 391 },
  { name: "Бишкек Юг", revenue: 96300, profit: 28100, avgCheck: 301, orders: 320 },
  { name: "Ош Парк", revenue: 74200, profit: 19800, avgCheck: 287, orders: 259 }
];

export const customers = [
  { name: "Айжан К.", phone: "+996 555 120 120", segment: "VIP", orders: 42, avg: 415, favorite: "Биг Бургер" },
  { name: "Нурбек Т.", phone: "+996 700 330 330", segment: "Постоянные", orders: 18, avg: 290, favorite: "Комбо Бургер" },
  { name: "Мээрим С.", phone: "+996 777 444 100", segment: "Новые", orders: 2, avg: 260, favorite: "Чизбургер" }
];

export const stockAlerts = [
  { item: "Котлета", branch: "Бишкек Центр", balance: "18 шт", threshold: "25 шт" },
  { item: "Сыр", branch: "Бишкек Юг", balance: "1.6 кг", threshold: "2 кг" },
  { item: "Стакан 0.5", branch: "Ош Парк", balance: "42 шт", threshold: "60 шт" }
];
