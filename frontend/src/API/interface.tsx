interface CategoryItem {
  name: string;
  id: number;
};

export interface Category {
    category_main: CategoryItem[];
    category_sport: CategoryItem[];
    category_accessories: CategoryItem[];
};

export interface ProductAllItem {
    id: number;
    categoryId: number;
    name: string;
    image: string;
    discountPercent: number;
    description: string;
    price: number;
    size: string;
    color: string;
    type: string;
};

export interface ProductAll {
    productList: ProductAllItem[];
};

export interface CategoryForProduct {
    name: string;
    categotyId: number;
};

export interface Product {
    id: number;
    name: string;
    description: string;
    price: number;
    discountPercent: number;
    stockQuantity: number;
    size: string[];
    color: string;
    gender: string;
    images: string[];
    category: CategoryForProduct;

};

export interface ReviewItem {
    username: string;
    rating: string;
    text: string;
};

export interface ReviewProduct {
    score: number;
    summary: string;
    reviews: ReviewItem[];
};

export interface AddBasket {
    product_id: number;
    size: string;
    score: number;
};

export interface DeleteBasket {
    product_id: number;
};

export interface BasketScore {
    score: number;
};

export interface Register {
    name: string;
    email: string;
    password: string;
};

export interface Authorization {
    email: string;
    password: string;
};

export interface ForgotPassword {
    email: string;
};

export interface Pickup {
    id: number;
    address: string;
};

export interface Order {
    firstName: string;
    lastName: string;
    email: string;
    phone: string;
    delivery: string;
    pay: string;
};

export interface UserInfo {
    name: string;
    email: string;
};

export interface OrderItem {
    id: number;
    date: string;
    total_amount: number;
    score: number;
    status_order: string;
};
