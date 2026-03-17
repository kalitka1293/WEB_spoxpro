import React from 'react'
import { Link } from 'react-router-dom'
import { Heart, Zap, Leaf, Users, Award, TrendingUp } from 'lucide-react'

const AboutPage: React.FC = () => (
  <div className="min-h-screen">

    {/* Hero */}
    <section className="relative h-[70vh] overflow-hidden">
      <img
        src="/img/clothes/kombez blue/kombez blue3.jpg"
        alt="spoXpro"
        className="w-full h-full object-cover"
      />
      <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/30 to-transparent" />
      <div className="absolute inset-0 flex items-end">
        <div className="container mx-auto px-4 pb-16">
          <h1 className="text-5xl md:text-7xl font-bold text-white mb-4 drop-shadow-lg">
            О нас
          </h1>
          <p className="text-xl md:text-2xl text-white/90 max-w-2xl drop-shadow-md">
            Мы создаём одежду, в которой хочется двигаться
          </p>
        </div>
      </div>
    </section>

    {/* Философия */}
    <section className="py-20 bg-white">
      <div className="container mx-auto px-4 max-w-5xl">
        <div className="grid md:grid-cols-2 gap-16 items-center">
          <div>
            <span className="text-sm font-semibold text-blue-600 uppercase tracking-widest mb-3 block">Философия</span>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6 leading-tight">
              Движение — это жизнь.<br />Мы делаем его комфортным.
            </h2>
            <p className="text-gray-600 leading-relaxed mb-4">
              spoXpro родился из простой идеи: спортивная одежда должна быть не только функциональной, но и красивой. Каждая вещь в нашей коллекции — это баланс между технологичностью и стилем.
            </p>
            <p className="text-gray-600 leading-relaxed">
              Мы работаем с передовыми материалами, которые дышат, отводят влагу и сохраняют форму даже после сотен стирок. Потому что вы заслуживаете лучшего.
            </p>
          </div>
          <div className="relative">
            <img
              src="/img/clothes/legensi and rashgard/legensi and rashgard1.jpg"
              alt="spoXpro quality"
              className="w-full rounded-2xl shadow-2xl"
            />
            <div className="absolute -bottom-6 -right-6 bg-blue-600 text-white px-6 py-4 rounded-xl shadow-lg">
              <div className="text-3xl font-bold">3+</div>
              <div className="text-sm text-blue-100">лет на рынке</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    {/* Цифры */}
    <section className="py-16 bg-gray-900 text-white">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
          <div>
            <div className="text-4xl md:text-5xl font-bold mb-2">500+</div>
            <div className="text-gray-400 text-sm">Товаров в каталоге</div>
          </div>
          <div>
            <div className="text-4xl md:text-5xl font-bold mb-2">10K+</div>
            <div className="text-gray-400 text-sm">Довольных клиентов</div>
          </div>
          <div>
            <div className="text-4xl md:text-5xl font-bold mb-2">4.8</div>
            <div className="text-gray-400 text-sm">Средняя оценка</div>
          </div>
          <div>
            <div className="text-4xl md:text-5xl font-bold mb-2">24/7</div>
            <div className="text-gray-400 text-sm">Поддержка</div>
          </div>
        </div>
      </div>
    </section>

    {/* Ценности */}
    <section className="py-20 bg-gray-50">
      <div className="container mx-auto px-4 max-w-5xl">
        <div className="text-center mb-14">
          <span className="text-sm font-semibold text-blue-600 uppercase tracking-widest mb-3 block">Ценности</span>
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900">Что нас определяет</h2>
        </div>
        <div className="grid md:grid-cols-3 gap-8">
          {[
            { icon: Zap, color: 'blue', title: 'Технологичность', text: 'Используем передовые ткани с влагоотводящими и антибактериальными свойствами' },
            { icon: Leaf, color: 'green', title: 'Экологичность', text: 'Стремимся к устойчивому производству и минимизации отходов' },
            { icon: Heart, color: 'red', title: 'Забота', text: 'Каждая деталь продумана для вашего максимального комфорта' },
            { icon: Users, color: 'purple', title: 'Сообщество', text: 'Объединяем людей, которые любят спорт и активный образ жизни' },
            { icon: Award, color: 'orange', title: 'Качество', text: 'Строгий контроль на каждом этапе — от ткани до готового изделия' },
            { icon: TrendingUp, color: 'teal', title: 'Развитие', text: 'Постоянно совершенствуем коллекции на основе обратной связи' },
          ].map((item, i) => (
            <div key={i} className="bg-white rounded-2xl p-8 shadow-sm hover:shadow-lg transition-shadow duration-300 group">
              <div className={`w-14 h-14 bg-${item.color}-100 rounded-xl flex items-center justify-center mb-5 group-hover:scale-110 transition-transform`}>
                <item.icon className={`h-7 w-7 text-${item.color}-600`} />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{item.title}</h3>
              <p className="text-gray-600 text-sm leading-relaxed">{item.text}</p>
            </div>
          ))}
        </div>
      </div>
    </section>

    {/* Визуальная секция */}
    <section className="py-20 bg-white">
      <div className="container mx-auto px-4 max-w-5xl">
        <div className="grid md:grid-cols-2 gap-6">
          <div className="relative rounded-2xl overflow-hidden aspect-[4/5]">
            <img src="/img/clothes/blue hudi/blue hudi1.jpg" alt="" className="w-full h-full object-cover" />
            <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
            <div className="absolute bottom-6 left-6 text-white">
              <div className="text-2xl font-bold">Стиль</div>
              <div className="text-white/80 text-sm">Для тех, кто ценит эстетику</div>
            </div>
          </div>
          <div className="grid grid-rows-1 gap-6">
            <div className="relative rounded-2xl overflow-hidden">
              <img src="/img/clothes/antracid/antracid1.jpg" alt="" className="w-full h-full object-cover" />
              <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
              <div className="absolute bottom-6 left-6 text-white">
                <div className="text-2xl font-bold">Комфорт</div>
                <div className="text-white/80 text-sm">В каждом движении</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    {/* CTA */}
    <section className="py-20 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
      <div className="container mx-auto px-4 text-center">
        <h2 className="text-3xl md:text-4xl font-bold mb-4">Присоединяйтесь к spoXpro</h2>
        <p className="text-xl text-blue-100 mb-10 max-w-2xl mx-auto">
          Откройте для себя одежду, которая вдохновляет на движение
        </p>
        <Link
          to="/catalog"
          className="bg-white text-blue-600 hover:bg-gray-100 text-lg px-10 py-4 rounded-full font-semibold hover:scale-105 transition-all duration-300 inline-block shadow-lg"
        >
          Перейти в каталог
        </Link>
      </div>
    </section>
  </div>
)

export default AboutPage
