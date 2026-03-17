import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { User, Mail, Phone, MapPin, Truck, Store, CreditCard, Banknote } from 'lucide-react'
import { postOrder, getPickup, getBasketUser, checkUser } from '@/API/RequestAPI'
import { Pickup, ProductAllItem } from '@/API/interface'
import { toast } from '@/components/Toast'

const CheckoutPage: React.FC = () => {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({ name: '', lastName: '', email: '', phone: '', address: '' })
  const [deliveryMethod, setDeliveryMethod] = useState<'delivery' | 'pickup'>('delivery')
  const [selectedPickup, setSelectedPickup] = useState<number | null>(null)
  const [paymentMethod, setPaymentMethod] = useState<'card' | 'cash'>('card')
  const [pickupPoints, setPickupPoints] = useState<Pickup[]>([])
  const [cartItems, setCartItems] = useState<ProductAllItem[]>([])

  useEffect(() => {
    const verifyAuth = async () => {
      const isAuth = await checkUser()
      if (!isAuth) navigate('/auth')
    }
    verifyAuth()

    const fetchPickup = async () => {
      try {
        const data = await getPickup()
        setPickupPoints(data as unknown as Pickup[])
      } catch (error) {
        console.error('Ошибка загрузки пунктов самовывоза:', error)
      }
    }
    const fetchBasket = async () => {
      try {
        const data = await getBasketUser()
        setCartItems((data as any).productList ?? data as unknown as ProductAllItem[])
      } catch (error) {
        console.error('Ошибка загрузки корзины:', error)
      }
    }
    fetchPickup()
    fetchBasket()
  }, [])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const handleSubmit = async () => {
    if (!formData.name || !formData.lastName || !formData.email || !formData.phone) {
      toast('Заполните все данные покупателя')
      return
    }
    const delivery = deliveryMethod === 'delivery' ? formData.address : String(selectedPickup ?? '')
    if (!delivery) {
      toast(deliveryMethod === 'delivery' ? 'Введите адрес доставки' : 'Выберите пункт самовывоза')
      return
    }
    const pay = paymentMethod === 'card' ? 'cart' : 'pickup'
    try {
      await postOrder({ firstName: formData.name, lastName: formData.lastName, email: formData.email, phone: formData.phone, delivery, pay })
      toast('Заказ оформлен', 'success')
      navigate('/profile')
    } catch (error) {
      console.error('Ошибка оформления заказа:', error)
      toast('Ошибка оформления заказа')
    }
  }

  const total = cartItems.reduce((sum, i) => sum + i.price, 0)

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Оформление заказа</h1>
        <div className="flex flex-col lg:flex-row gap-8">

          {/* Левая часть */}
          <div className="lg:w-2/3 space-y-6">
            {/* Данные покупателя */}
            <div className="card p-6 bg-white">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Данные покупателя</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Имя</label>
                  <div className="relative">
                    <User className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <input name="name" value={formData.name} onChange={handleChange} className="input pl-10" placeholder="Имя" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Фамилия</label>
                  <div className="relative">
                    <User className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <input name="lastName" value={formData.lastName} onChange={handleChange} className="input pl-10" placeholder="Фамилия" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <input name="email" type="email" value={formData.email} onChange={handleChange} className="input pl-10" placeholder="your@email.com" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Телефон</label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <input name="phone" value={formData.phone} onChange={handleChange} className="input pl-10" placeholder="+7 (999) 999-99-99" />
                  </div>
                </div>
              </div>
            </div>

            {/* Способ получения */}
            <div className="card p-6 bg-white">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Способ получения</h2>
              <div className="flex gap-4 mb-4">
                <button
                  onClick={() => setDeliveryMethod('delivery')}
                  className={`flex-1 flex items-center justify-center py-3 px-4 border rounded-lg transition-colors ${deliveryMethod === 'delivery' ? 'border-blue-500 bg-blue-50 text-blue-600' : 'border-gray-300 text-gray-700 hover:border-gray-400'}`}
                >
                  <Truck className="h-5 w-5 mr-2" />
                  Доставка
                </button>
                <button
                  onClick={() => setDeliveryMethod('pickup')}
                  className={`flex-1 flex items-center justify-center py-3 px-4 border rounded-lg transition-colors ${deliveryMethod === 'pickup' ? 'border-blue-500 bg-blue-50 text-blue-600' : 'border-gray-300 text-gray-700 hover:border-gray-400'}`}
                >
                  <Store className="h-5 w-5 mr-2" />
                  Самовывоз
                </button>
              </div>

              {deliveryMethod === 'delivery' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Адрес доставки</label>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <input name="address" value={formData.address} onChange={handleChange} className="input pl-10" placeholder="Город, улица, дом, квартира" />
                  </div>
                </div>
              )}

              {deliveryMethod === 'pickup' && (
                <div className="space-y-3">
                  {pickupPoints.map(point => (
                    <button
                      key={point.id}
                      onClick={() => setSelectedPickup(point.id)}
                      className={`w-full text-left p-4 border rounded-lg transition-colors ${selectedPickup === point.id ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}`}
                    >
                      <p className="font-medium text-gray-900">{point.address}</p>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Способ оплаты */}
            <div className="card p-6 bg-white">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Способ оплаты</h2>
              <div className="flex gap-4">
                <button
                  onClick={() => setPaymentMethod('card')}
                  className={`flex-1 flex items-center justify-center py-3 px-4 border rounded-lg transition-colors ${paymentMethod === 'card' ? 'border-blue-500 bg-blue-50 text-blue-600' : 'border-gray-300 text-gray-700 hover:border-gray-400'}`}
                >
                  <CreditCard className="h-5 w-5 mr-2" />
                  Картой онлайн
                </button>
                <button
                  onClick={() => setPaymentMethod('cash')}
                  className={`flex-1 flex items-center justify-center py-3 px-4 border rounded-lg transition-colors ${paymentMethod === 'cash' ? 'border-blue-500 bg-blue-50 text-blue-600' : 'border-gray-300 text-gray-700 hover:border-gray-400'}`}
                >
                  <Banknote className="h-5 w-5 mr-2" />
                  При получении
                </button>
              </div>
            </div>
          </div>

          {/* Правая часть — Ваш заказ */}
          <div className="lg:w-1/3">
            <div className="card p-6 bg-white sticky top-24">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Ваш заказ</h2>
              <div className="space-y-4 mb-6">
                {cartItems.map(item => (
                  <div key={item.id} className="flex items-center gap-3">
                    <div className="w-14 h-14 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0">
                      <img src={item.image} alt={item.name} className="w-full h-full object-cover" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{item.name}</p>
                      <p className="text-xs text-gray-600">{item.size}</p>
                    </div>
                    <span className="text-sm font-bold text-gray-900">{item.price}₽</span>
                  </div>
                ))}
              </div>
              <div className="border-t border-gray-200 pt-4 space-y-2">
                <div className="flex justify-between text-sm text-gray-600">
                  <span>Стоимость доставки</span>
                  <span className="text-green-600 font-medium">Бесплатно</span>
                </div>
                <div className="flex justify-between text-lg font-bold text-gray-900">
                  <span>Итого:</span>
                  <span>{total.toLocaleString('ru-RU')} ₽</span>
                </div>
              </div>
              <button onClick={handleSubmit} className="w-full btn-primary text-lg py-4 mt-6">
                Подтвердить заказ
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CheckoutPage
