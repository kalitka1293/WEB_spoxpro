import React from 'react'

const ReturnsPage: React.FC = () => (
  <div className="min-h-screen bg-gray-50">
    <div className="container mx-auto px-4 py-12 max-w-4xl">
      <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-8">Возврат и обмен</h1>
      <div className="card bg-white p-8 space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">Условия возврата</h2>
          <ul className="text-gray-600 space-y-2">
            <li>• Возврат товара возможен в течение 14 дней с момента получения</li>
            <li>• Товар должен сохранить товарный вид, бирки и упаковку</li>
            <li>• Товар не должен иметь следов использования</li>
          </ul>
        </div>
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">Как оформить возврат</h2>
          <ol className="text-gray-600 space-y-2 list-decimal list-inside">
            <li>Свяжитесь с нами по телефону или email</li>
            <li>Укажите номер заказа и причину возврата</li>
            <li>Отправьте товар по указанному адресу</li>
            <li>Возврат средств — в течение 10 рабочих дней</li>
          </ol>
        </div>
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">Обмен товара</h2>
          <p className="text-gray-600">
            Обмен на другой размер или цвет осуществляется бесплатно. Свяжитесь с нами, и мы организуем обмен в кратчайшие сроки.
          </p>
        </div>
      </div>
    </div>
  </div>
)

export default ReturnsPage
