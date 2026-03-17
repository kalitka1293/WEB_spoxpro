import { apiClient } from "./client";
import { 
    Category,
    ProductAll,
    Product,
    ReviewProduct,
    AddBasket,
    BasketScore,
    Register,
    Authorization,
    ForgotPassword,
    Pickup,
    Order,
    DeleteBasket,
    UserInfo,
    OrderItem
} from "./interface";


export const getCsrfToken = async (): Promise<void> => {
  await apiClient.get('/auth/csrf-token');
};

export const postRefreshToken = async (): Promise<void> => {
  await apiClient.post('/auth/refresh');
};


export const checkUser = async (): Promise<boolean> => {

    try {
        await apiClient.get('/user/check');
        return true;
    } catch {
        return false;
    }
}; 

export const getUserInfo = async (): Promise<UserInfo> => {
    const { data } = await apiClient.get('/user/info');
    return data;
};

export const getOrder = async (): Promise<OrderItem[]> => {
    const { data } = await apiClient.get('/basket/get_order');
    return data;
};

export const postOrder = async ( formData: Order): Promise<Order> => {

    await getCsrfToken();

    const { data } = await apiClient.post('/basket/order', formData) 
    return data
};

export const getPickup = async (): Promise<Pickup> => {
    const { data } = await apiClient.get('/store/pickup')
    return data;
};

export const postForgotPassword = async ( formData: ForgotPassword): Promise<ForgotPassword> => {

    await getCsrfToken();

    const { data } = await apiClient.post('/auth/forgot_password', formData) 
    return data
};

export const postAuthorization = async ( formData: Authorization): Promise<Authorization> => {

    await getCsrfToken();

    const { data } = await apiClient.post('/auth/authorization', formData) 
    return data
};

export const postRegister = async ( formData: Register): Promise<Register> => {

    await getCsrfToken();

    const { data } = await apiClient.post('/auth/register', formData) 
    return data
};

export const deleteBasketUser = async (product_id: number): Promise<DeleteBasket> => {

    await getCsrfToken();

    const { data } = await apiClient.delete('/basket/delete', { params: {product_id}})
    return data;
};

export const getBasketUser = async (): Promise<ProductAll> => {
    const { data } = await apiClient.get('/basket/get_basket')
    return data;
};

export const getBasketScore = async (): Promise<BasketScore> => {
    const { data } = await apiClient.get('/basket/score_basket')
    return data;
};

export const postAddBasket = async (basketData: AddBasket): Promise<AddBasket> => {

    await getCsrfToken();

    const { data } = await apiClient.post('/basket/add', basketData);
    return data;
};

export const getReviewById = async (product_id: number): Promise<ReviewProduct> => {
    const { data } = await apiClient.get('/review/product_review', {params: { product_id }})
    return data;
};

export const getProductById = async (product_id: number): Promise<Product> => {
    const { data } = await apiClient.get('/store/product', {params: { product_id }})
    return data;
};

export const getCategory = async (): Promise<Category> => {
    const { data } = await apiClient.get('/store/category');
    return data;
};

export const getAllProduct = async (score: number = 0): Promise<ProductAll> => {
    if (score == 0){
        const { data } = await apiClient.get('/store/allproduct')
        return data;
    }else{
        const { data } = await apiClient.get('/store/allproduct', {params: { score }})
        return data;
    }
};