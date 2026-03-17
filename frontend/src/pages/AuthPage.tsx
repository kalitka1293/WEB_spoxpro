import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, User, Mail, Lock, Phone, MapPin } from 'lucide-react'
import { postRegister, postAuthorization } from '@/API/RequestAPI'
import { toast } from '@/components/Toast'

const AuthPage: React.FC = () => {
  const navigate = useNavigate()
  const [isLogin, setIsLogin] = useState(true)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    name: '',
    lastName: '',
    phone: '',
    address: '',
    country: 'Россия'
  })

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (isLogin) {
      try {
        await postAuthorization({ email: formData.email, password: formData.password })
        navigate('/catalog')
      } catch (error) {
        console.error('Ошибка авторизации:', error)
        toast('Ошибка авторизации')
      }
    } else {
      if (formData.password.length < 6) {
        toast('Пароль должен быть не менее 6 символов')
        return
      }
      if (formData.password !== formData.confirmPassword) {
        toast('Пароли не совпадают')
        return
      }
      try {
        await postRegister({ name: formData.name, email: formData.email, password: formData.password })
        toast('Регистрация успешна', 'success')
        setIsLogin(true)
      } catch (error) {
        console.error('Ошибка регистрации:', error)
        toast('Ошибка регистрации')
      }
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center space-x-3">
            <img 
              src="/img/logo/logo.png" 
              alt="spoXpro Logo" 
              className="h-12 w-auto"
            />
            <img 
              src="/img/name/name.png" 
              alt="spoXpro" 
              className="h-8 w-auto"
            />
          </Link>
          <h2 className="mt-6 text-3xl font-bold text-gray-900">
            {isLogin ? 'Вход в аккаунт' : 'Создать аккаунт'}
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            {isLogin 
              ? 'Войдите в свой аккаунт для продолжения покупок' 
              : 'Зарегистрируйтесь для получения персональных предложений'
            }
          </p>
        </div>

        <div className="card p-8 bg-white">
          <form onSubmit={handleSubmit} className="space-y-6">
            {!isLogin && (
              <>
                {/* Имя */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                      Имя
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <input
                        id="name"
                        name="name"
                        type="text"
                        required={!isLogin}
                        value={formData.name}
                        onChange={handleInputChange}
                        className="input pl-10"
                        placeholder="Ваше имя"
                      />
                    </div>
                  </div>
                </div>
              </>
            )}

            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  value={formData.email}
                  onChange={handleInputChange}
                  className="input pl-10"
                  placeholder="your@email.com"
                />
              </div>
            </div>

            {/* Пароль */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                Пароль
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={formData.password}
                  onChange={handleInputChange}
                  className="input pl-10 pr-10"
                  placeholder="Введите пароль"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {/* Подтверждение пароля для регистрации */}
            {!isLogin && (
              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">
                  Подтвердите пароль
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <input
                    id="confirmPassword"
                    name="confirmPassword"
                    type={showConfirmPassword ? 'text' : 'password'}
                    required={!isLogin}
                    value={formData.confirmPassword}
                    onChange={handleInputChange}
                    className="input pl-10 pr-10"
                    placeholder="Повторите пароль"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
                  >
                    {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
            )}

            {/* Забыли пароль для входа */}
            {isLogin && (
              <div className="flex items-center justify-between">
                <label className="flex items-center">
                  <input type="checkbox" className="mr-2" />
                  <span className="text-sm text-gray-600">Запомнить меня</span>
                </label>
                <Link to="/forgot-password" className="text-sm text-blue-600 hover:underline">
                  Забыли пароль?
                </Link>
              </div>
            )}

            {/* Согласие на обработку данных для регистрации */}
            {!isLogin && (
              <div className="flex items-start">
                <input type="checkbox" required className="mt-1 mr-3" />
                <span className="text-sm text-gray-600">
                  Я согласен с{' '}
                  <Link to="/terms" className="text-blue-600 hover:underline">
                    пользовательским соглашением
                  </Link>{' '}
                  и{' '}
                  <Link to="/privacy" className="text-blue-600 hover:underline">
                    политикой конфиденциальности
                  </Link>
                </span>
              </div>
            )}

            {/* Кнопка отправки */}
            <button type="submit" className="w-full btn-primary text-lg py-3">
              {isLogin ? 'Войти' : 'Зарегистрироваться'}
            </button>
          </form>

          {/* Переключение между входом и регистрацией */}
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              {isLogin ? 'Нет аккаунта?' : 'Уже есть аккаунт?'}{' '}
              <button
                onClick={() => setIsLogin(!isLogin)}
                className="text-blue-600 hover:underline font-medium"
              >
                {isLogin ? 'Зарегистрироваться' : 'Войти'}
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AuthPage
