import React from 'react'

const PrivacyPage: React.FC = () => (
  <div className="min-h-screen bg-gray-50">
    <div className="container mx-auto px-4 py-12 max-w-4xl">
      <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-8">Политика конфиденциальности</h1>
      <div className="card bg-white p-8 space-y-6 text-gray-600 leading-relaxed">
        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">1. Общие положения</h2>
          <p>Настоящая Политика конфиденциальности определяет порядок обработки и защиты персональных данных пользователей сайта spoXpro. Используя сайт, вы соглашаетесь с условиями данной политики.</p>
        </section>
        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">2. Сбор данных</h2>
          <p>Мы собираем следующие данные: имя, email, номер телефона, адрес доставки — исключительно для обработки заказов и улучшения качества обслуживания.</p>
        </section>
        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">3. Использование данных</h2>
          <p>Персональные данные используются для оформления и доставки заказов, связи с клиентом, улучшения работы сайта. Мы не передаём данные третьим лицам без вашего согласия.</p>
        </section>
        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">4. Защита данных</h2>
          <p>Мы применяем современные методы защиты информации для предотвращения несанкционированного доступа к персональным данным.</p>
        </section>
        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">5. Контакты</h2>
          <p>По вопросам обработки персональных данных обращайтесь: info@spoxpro.ru</p>
        </section>
      </div>
    </div>
  </div>
)

export default PrivacyPage
