import React from 'react'
import { Truck, CreditCard, Banknote } from 'lucide-react'

const DeliveryPage: React.FC = () => (
  <div className="min-h-screen bg-gray-50">
    <div className="container mx-auto px-4 py-12 max-w-4xl">
      <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-8">Доставка и оплата</h1>

      <div className="space-y-6">
        <div className="card bg-white p-8">
          <div className="flex items-center mb-4">
            <Truck className="h-6 w-6 text-blue-600 mr-3" />
            <h2 className="text-xl font-semibold text-gray-900">Способы доставки</h2>
          </div>
          <div className="space-y-4 text-gray-600">
            <div className="p-4 bg-gray-50 rounded-lg">
              <h3 className="font-medium text-gray-900 mb-1">Курьерская доставка</h3>
              <p>Доставка по Москве — бесплатно. Срок: 1–2 рабочих дня.</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <h3 className="font-medium text-gray-900 mb-1">Доставка по России</h3>
              <p>Бесплатная доставка по всей России. Срок: 3–7 рабочих дней.</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <h3 className="font-medium text-gray-900 mb-1">Самовывоз</h3>
              <p>Забрать заказ можно из пункта выдачи. Готовность — в день заказа.</p>
            </div>
          </div>
        </div>

        <div className="card bg-white p-8">
          <div className="flex items-center mb-4">
            <CreditCard className="h-6 w-6 text-blue-600 mr-3" />
            <h2 className="text-xl font-semibold text-gray-900">Способы оплаты</h2>
          </div>
          <div className="space-y-4 text-gray-600">
            <div className="p-4 bg-gray-50 rounded-lg flex items-center">
              <CreditCard className="h-5 w-5 text-gray-500 mr-3" />
              <div>
                <h3 className="font-medium text-gray-900">Банковская карта</h3>
                <p className="text-sm">Visa, MasterCard, МИР</p>
              </div>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg flex items-center">
              <Banknote className="h-5 w-5 text-gray-500 mr-3" />
              <div>
                <h3 className="font-medium text-gray-900">Наличные</h3>
                <p className="text-sm">Оплата при получении</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
)

export default DeliveryPage
