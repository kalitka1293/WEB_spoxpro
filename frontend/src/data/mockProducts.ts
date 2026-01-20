import { Product, CLOTHING_CATEGORIES } from '../types/product';

// Генерируем моковые товары на основе доступных изображений
export const mockProducts: Product[] = [
  // Антрацитовая коллекция (11 фото)
  {
    id: '1',
    name: 'Антрацитовый спортивный костюм',
    description: 'Стильный спортивный костюм в антрацитовом цвете. Идеально подходит для тренировок и повседневной носки.',
    price: 4990,
    stockQuantity: 15,
    size: 'M',
    color: 'Антрацит',
    gender: 'U',
    discountPercent: 0,
    categoryId: 9,
    category: CLOTHING_CATEGORIES[8],
    images: Array.from({length: 11}, (_, i) => `/img/clothes/antracid/antracid${i + 1}.jpg`),
    createdAt: '2024-01-15T10:00:00Z'
  },
  
  // Синие худи (8 фото)
  {
    id: '2',
    name: 'Синее худи spoXpro',
    description: 'Комфортное худи из премиального хлопка. Отлично сочетается с любой спортивной одеждой.',
    price: 3490,
    stockQuantity: 20,
    size: 'L',
    color: 'Синий',
    gender: 'U',
    discountPercent: 0,
    categoryId: 7,
    category: CLOTHING_CATEGORIES[6],
    images: Array.from({length: 8}, (_, i) => `/img/clothes/blue hudi/blue hudi${i + 1}.jpg`),
    createdAt: '2024-01-20T10:00:00Z'
  },
  
  // Синие легинсы и топы (8 фото)
  {
    id: '3',
    name: 'Комплект: синие легинсы и топ',
    description: 'Спортивный комплект из дышащих материалов. Идеален для фитнеса, йоги и активного отдыха.',
    price: 5490,
    stockQuantity: 12,
    size: 'S',
    color: 'Синий',
    gender: 'F',
    discountPercent: 0,
    categoryId: 3,
    category: CLOTHING_CATEGORIES[2],
    images: Array.from({length: 8}, (_, i) => `/img/clothes/blue losini and top/blue losini and top${i + 1}.jpg`),
    createdAt: '2024-01-25T10:00:00Z'
  },
  
  // Синие комбинезоны (18 фото)
  {
    id: '4',
    name: 'Синий спортивный комбинезон',
    description: 'Стильный комбинезон для активных тренировок. Обеспечивает максимальную свободу движений.',
    price: 6990,
    stockQuantity: 8,
    size: 'M',
    color: 'Синий',
    gender: 'F',
    discountPercent: 0,
    categoryId: 1,
    category: CLOTHING_CATEGORIES[0],
    images: Array.from({length: 18}, (_, i) => `/img/clothes/kombez blue/kombez blue${i + 1}.jpg`),
    createdAt: '2024-02-01T10:00:00Z'
  },
  
  // Легинсы и рашгарды
  {
    id: '5',
    name: 'Комплект: легинсы и рашгард',
    description: 'Функциональный комплект для интенсивных тренировок. Отводит влагу и обеспечивает компрессию.',
    price: 4790,
    stockQuantity: 18,
    size: 'M',
    color: 'Мультиколор',
    gender: 'F',
    discountPercent: 0,
    categoryId: 10,
    category: CLOTHING_CATEGORIES[9],
    images: Array.from({length: 11}, (_, i) => `/img/clothes/legensi and rashgard/legensi and rashgard${i + 1}.jpg`),
    createdAt: '2024-02-05T10:00:00Z'
  },
  
  // Шаровары и топы
  {
    id: '6',
    name: 'Комплект: шаровары и топ',
    description: 'Свободный комплект для йоги и медитации. Натуральные материалы и максимальный комфорт.',
    price: 3990,
    stockQuantity: 14,
    size: 'L',
    color: 'Бежевый',
    gender: 'F',
    discountPercent: 0,
    categoryId: 15,
    category: CLOTHING_CATEGORIES[14],
    images: Array.from({length: 8}, (_, i) => `/img/clothes/sharovari and top/sharovari and top${i + 1}.jpg`),
    createdAt: '2024-02-10T10:00:00Z'
  },
  
  // Шорты Siren
  {
    id: '7',
    name: 'Шорты Siren Premium',
    description: 'Премиальные спортивные шорты с технологией влагоотведения. Для самых требовательных спортсменов.',
    price: 2990,
    stockQuantity: 25,
    size: 'S',
    color: 'Черный',
    gender: 'F',
    discountPercent: 0,
    categoryId: 14,
    category: CLOTHING_CATEGORIES[13],
    images: Array.from({length: 6}, (_, i) => `/img/clothes/siren shorts/siren shorts${i + 1}.jpg`),
    createdAt: '2024-02-15T10:00:00Z'
  },
  
  // Белые худи
  {
    id: '8',
    name: 'Белое худи Classic',
    description: 'Классическое белое худи из органического хлопка. Базовая вещь для любого гардероба.',
    price: 3290,
    stockQuantity: 22,
    size: 'M',
    color: 'Белый',
    gender: 'U',
    discountPercent: 0,
    categoryId: 17,
    category: CLOTHING_CATEGORIES[16],
    images: Array.from({length: 7}, (_, i) => `/img/clothes/white hudi/white hudi${i + 1}.jpg`),
    createdAt: '2024-02-20T10:00:00Z'
  },
  
  // Кофты и брюки
  {
    id: '9',
    name: 'Комплект: кофта на молнии и брюки',
    description: 'Практичный спортивный костюм с кофтой на молнии. Отлично подходит для разминки и отдыха.',
    price: 5790,
    stockQuantity: 16,
    size: 'L',
    color: 'Серый',
    gender: 'U',
    discountPercent: 0,
    categoryId: 8,
    category: CLOTHING_CATEGORIES[7],
    images: Array.from({length: 9}, (_, i) => `/img/clothes/zip and bruki/zip and bruki${i + 1}.jpg`),
    createdAt: '2024-02-25T10:00:00Z'
  }
];

// Функция для получения товаров по категории
export const getProductsByCategory = (categoryId: number): Product[] => {
  return mockProducts.filter(product => product.categoryId === categoryId);
};

// Функция для получения товара по ID
export const getProductById = (id: string): Product | undefined => {
  return mockProducts.find(product => product.id === id);
};

// Функция для получения товаров со скидкой
export const getDiscountedProducts = (): Product[] => {
  return mockProducts.filter(product => product.discountPercent > 0);
};
