export interface Product {
  id: string;
  name: string;
  description: string;
  price: number;
  stockQuantity: number;
  size: string;
  color: string;
  gender: 'M' | 'F' | 'U';
  discountPercent: number;
  categoryId: number;
  category: Category;
  images: string[];
  createdAt: string;
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  parentId?: number;
  parent?: Category;
  children?: Category[];
}

export interface CartItem {
  id: string;
  product: Product;
  quantity: number;
  size: string;
}

export interface User {
  id: string;
  name: string;
  lastName: string;
  email: string;
  phone: string;
  address: string;
  isAdmin: boolean;
}

// Категории одежды
export const CLOTHING_CATEGORIES = [
  {
    id: 1,
    name: 'Комбинезоны',
    slug: 'kombez-blue',
    folder: 'kombez blue',
    description: 'Стильные комбинезоны для спорта'
  },
  {
    id: 2,
    name: 'Топы-бра',
    slug: 'blue-losini-top',
    folder: 'blue losini and top',
    description: 'Спортивные топы-бра'
  },
  {
    id: 3,
    name: 'Леггинсы',
    slug: 'legensi-rashgard',
    folder: 'legensi and rashgard',
    description: 'Функциональные леггинсы для тренировок'
  },
  {
    id: 4,
    name: 'Куртки',
    slug: 'zip-bruki',
    folder: 'zip and bruki',
    description: 'Спортивные куртки и ветровки'
  },
  {
    id: 5,
    name: 'Кроссовки',
    slug: 'krossovki',
    folder: 'antracid',
    description: 'Спортивная обувь'
  },
  {
    id: 6,
    name: 'Свитшоты',
    slug: 'svitshoty',
    folder: 'antracid',
    description: 'Комфортные свитшоты'
  },
  {
    id: 7,
    name: 'Худи',
    slug: 'blue-hudi',
    folder: 'blue hudi',
    description: 'Комфортные худи'
  },
  {
    id: 8,
    name: 'Брюки',
    slug: 'bruki',
    folder: 'zip and bruki',
    description: 'Спортивные брюки'
  },
  {
    id: 9,
    name: 'Костюмы',
    slug: 'antracid',
    folder: 'antracid',
    description: 'Спортивные костюмы'
  },
  {
    id: 10,
    name: 'Рашгарды',
    slug: 'rashgardy',
    folder: 'legensi and rashgard',
    description: 'Рашгарды для тренировок'
  },
  {
    id: 11,
    name: 'Боди',
    slug: 'bodi',
    folder: 'blue losini and top',
    description: 'Спортивные боди'
  },
  {
    id: 12,
    name: 'Футболки и майки',
    slug: 'futbolki',
    folder: 'blue losini and top',
    description: 'Футболки и майки для спорта'
  },
  {
    id: 13,
    name: 'Велосипедки',
    slug: 'velosipedki',
    folder: 'siren shorts',
    description: 'Короткие велосипедки'
  },
  {
    id: 14,
    name: 'Шорты',
    slug: 'siren-shorts',
    folder: 'siren shorts',
    description: 'Спортивные шорты'
  },
  {
    id: 15,
    name: 'Платья и юбки',
    slug: 'platya-yubki',
    folder: 'sharovari and top',
    description: 'Спортивные платья и юбки'
  },
  {
    id: 16,
    name: 'Купальники',
    slug: 'kupalniki',
    folder: 'blue losini and top',
    description: 'Купальники для плавания'
  },
  {
    id: 17,
    name: 'Лонгсливы',
    slug: 'longsliv',
    folder: 'white hudi',
    description: 'Лонгсливы с длинным рукавом'
  }
] as const;
