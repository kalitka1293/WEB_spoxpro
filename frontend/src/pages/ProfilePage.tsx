import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { ShoppingBag, Package, Trash2 } from 'lucide-react'
import { getBasketUser, deleteBasketUser, getUserInfo, getOrder } from '@/API/RequestAPI'
import { ProductAllItem, UserInfo, OrderItem } from '@/API/interface'

const ProfilePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'basket' | 'orders'>('basket')
  const [basket, setBasket] = useState<ProductAllItem[]>([])
  const [user, setUser] = useState<UserInfo | null>(null)
  const [orders, setOrders] = useState<OrderItem[]>([])

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const data = await getUserInfo()
        setUser(data)
      } catch (error) {
        console.error('Ошибка загрузки пользователя:', error)
      }
    }
    fetchUser()

    const fetchOrders = async () => {
      try {
        const data = await getOrder()
        setOrders(Array.isArray(data) ? data : [])
      } catch (error) {
        console.error('Ошибка загрузки заказов:', error)
      }
    }
    fetchOrders()

    const fetchBasket = async () => {
      try {
        const data = await getBasketUser()
        const list = Array.isArray(data) ? data : (data as any).productList ?? []
        setBasket(list as ProductAllItem[])
      } catch (error) {
        console.error('Ошибка загрузки корзины:', error)
      }
    }
    fetchBasket()
  }, [])

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col lg:flex-row gap-8">

          {/* Левая панель — профиль */}
          <div className="lg:w-1/4">
            <div className="card p-6 bg-white">
              <div className="flex items-center mb-4">
                <div className="w-16 h-16 rounded-full overflow-hidden mr-4">
                  <img src="/img/logo/logo.png" alt="avatar" className="w-full h-full object-cover" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">{user?.name}</h2>
                  <p className="text-sm text-gray-600">{user?.email}</p>
                </div>
              </div>
              <div className="space-y-2 mt-6">
                <button
                  onClick={() => setActiveTab('basket')}
                  className={`w-full text-left px-4 py-3 rounded-lg flex items-center transition-colors ${activeTab === 'basket' ? 'bg-blue-50 text-blue-600' : 'text-gray-700 hover:bg-gray-100'}`}
                >
                  <ShoppingBag className="h-5 w-5 mr-3" />
                  Корзина
                </button>
                <button
                  onClick={() => setActiveTab('orders')}
                  className={`w-full text-left px-4 py-3 rounded-lg flex items-center transition-colors ${activeTab === 'orders' ? 'bg-blue-50 text-blue-600' : 'text-gray-700 hover:bg-gray-100'}`}
                >
                  <Package className="h-5 w-5 mr-3" />
                  Заказы
                </button>
              </div>
            </div>
          </div>

          {/* Правая панель — контент */}
          <div className="lg:w-3/4">
            {activeTab === 'basket' && (
              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-6">Корзина</h2>
                <Link to="/checkout" className="w-full btn-primary text-lg py-4 mb-6 flex items-center justify-center">
                  <Package className="h-5 w-5 mr-2" />
                  Оформить заказ
                </Link>
                {basket.length === 0 ? (
                  <div className="card p-8 bg-white text-center">
                    <p className="text-gray-600">Корзина пуста</p>
                    <Link to="/catalog" className="btn-primary mt-4 inline-block">Перейти в каталог</Link>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {basket.map(item => (
                      <div key={item.id} className="card p-4 bg-white flex items-center gap-4">
                        <div className="w-20 h-20 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0">
                          <img src={item.image} alt={item.name} className="w-full h-full object-cover" />
                        </div>
                        <div className="flex-1">
                          <h3 className="font-semibold text-gray-900">{item.name}</h3>
                          <p className="text-sm text-gray-600">Размер: {item.size} • Цвет: {item.color}</p>
                        </div>
                        <span className="text-lg font-bold text-gray-900">{item.price}₽</span>
                        <button
                          onClick={async () => {
                            try {
                              await deleteBasketUser(item.id)
                              setBasket(b => b.filter(i => i.id !== item.id))
                              window.dispatchEvent(new Event('cart-updated'))
                            } catch (e) { console.error(e) }
                          }}
                          className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                    <div className="card p-4 bg-white flex justify-between items-center">
                      <span className="text-lg font-semibold text-gray-900">Итого:</span>
                      <span className="text-xl font-bold text-gray-900">{basket.reduce((sum, i) => sum + i.price, 0)}₽</span>
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'orders' && (
              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-6">Заказы</h2>
                {orders.length === 0 ? (
                  <div className="card p-8 bg-white text-center">
                    <p className="text-gray-600">Заказов пока нет</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {orders.map(order => (
                      <div key={order.id} className="card p-6 bg-white">
                        <div className="flex justify-between items-center mb-2">
                          <span className="font-semibold text-gray-900">Заказ #{order.id}</span>
                          <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">{order.status_order}</span>
                        </div>
                        <div className="flex justify-between text-sm text-gray-600">
                          <span>{order.date}</span>
                          <span>Кол-во: {order.score}</span>
                        </div>
                        <div className="mt-2 pt-2 border-t border-gray-200 flex justify-end">
                          <span className="font-bold text-gray-900">{order.total_amount}₽</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ProfilePage
