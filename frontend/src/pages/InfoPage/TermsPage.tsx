import React from 'react'

const TermsPage: React.FC = () => (
  <div className="min-h-screen bg-gray-50">
    <div className="container mx-auto px-4 py-12 max-w-4xl">
      <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-8">Пользовательское соглашение</h1>
      <div className="card bg-white p-8 space-y-6 text-gray-600 leading-relaxed">
        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">1. Общие условия</h2>
          <p>Настоящее соглашение регулирует отношения между администрацией сайта spoXpro и пользователем. Использование сайта означает согласие с данными условиями.</p>
        </section>
        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">2. Права и обязанности</h2>
          <p>Пользователь обязуется предоставлять достоверную информацию при оформлении заказа. Администрация обязуется обеспечить надлежащее качество товаров и услуг.</p>
        </section>
        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">3. Оформление заказа</h2>
          <p>Заказ считается оформленным после подтверждения на сайте. Цены на товары указаны в рублях и включают НДС.</p>
        </section>
        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">4. Ответственность</h2>
          <p>Администрация не несёт ответственности за временную недоступность сайта по техническим причинам. Все споры решаются путём переговоров.</p>
        </section>
        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">5. Изменение условий</h2>
          <p>Администрация оставляет за собой право изменять условия соглашения. Актуальная версия всегда доступна на данной странице.</p>
        </section>
      </div>
    </div>
  </div>
)

export default TermsPage
