import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Trash2, ShoppingBag, ArrowRight } from 'lucide-react'
import { getBasketUser, deleteBasketUser } from '@/API/RequestAPI'
import { ProductAllItem } from '@/API/interface'

const CartPage: React.FC = () => {
  const [cartItems, setCartItems] = useState<ProductAllItem[]>([])

  useEffect(() => {
    const fetchBasket = async () => {
      try {
        const data = await getBasketUser()
        const list = Array.isArray(data) ? data : (data as any).productList ?? []
        setCartItems(list as ProductAllItem[])
      } catch (error) {
        console.error('Ошибка загрузки корзины:', error)
      }
    }
    fetchBasket()
  }, [])

  const removeItem = async (id: number) => {
    try {
      await deleteBasketUser(id)
      setCartItems(items => items.filter(item => item.id !== id))
      window.dispatchEvent(new Event('cart-updated'))
    } catch (error) {
      console.error('Ошибка удаления:', error)
    }
  }

  const total = cartItems.reduce((sum, item) => sum + item.price, 0)

  if (cartItems.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="container mx-auto px-4 py-16">
          <div className="max-w-md mx-auto text-center">
            <div className="w-24 h-24 bg-gray-200 rounded-full mx-auto mb-6 flex items-center justify-center">
              <ShoppingBag className="h-12 w-12 text-gray-400" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-4">
              Корзина пуста
            </h1>
            <p className="text-gray-600 mb-8">
              Добавьте товары в корзину, чтобы оформить заказ
            </p>
            <Link to="/catalog" className="btn-primary">
              Перейти к покупкам
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          Корзина ({cartItems.length})
        </h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Товары в корзине */}
          <div className="lg:col-span-2 space-y-4">
            {cartItems.map((item) => (
              <div key={item.id} className="card p-6 bg-white">
                <div className="flex items-start space-x-4">
                  <img
                    src={item.image}
                    alt={item.name}
                    className="w-24 h-24 object-cover rounded-lg"
                  />
                  
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      {item.name}
                    </h3>
                    <p className="text-sm text-gray-600 mb-2">
                      Размер: {item.size} • Цвет: {item.color}
                    </p>
                    <p className="text-lg font-bold text-gray-900">
                      {item.price}₽
                    </p>
                  </div>

                  <button
                    onClick={() => removeItem(item.id)}
                    className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Итоги заказа */}
          <div className="lg:col-span-1">
            <div className="card p-6 bg-white sticky top-24">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">
                Итоги заказа
              </h2>
              
              <div className="space-y-4 mb-6">
                <div className="flex justify-between">
                  <span className="text-gray-600">Товары ({cartItems.length})</span>
                  <span className="font-medium">{total}₽</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Доставка</span>
                  <span className="font-medium">Бесплатно</span>
                </div>
                <div className="border-t pt-4">
                  <div className="flex justify-between text-lg font-bold">
                    <span>Итого</span>
                    <span>{total}₽</span>
                  </div>
                </div>
              </div>

              <Link to="/checkout" className="w-full btn-primary text-lg py-4 mb-4 flex items-center justify-center">
                Оформить заказ
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
              
              <Link 
                to="/catalog"
                className="block text-center text-blue-600 hover:underline"
              >
                Продолжить покупки
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CartPage
