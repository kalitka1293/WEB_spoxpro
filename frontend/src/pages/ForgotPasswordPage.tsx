import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { Mail } from 'lucide-react'
import { postForgotPassword } from '@/API/RequestAPI'
import { toast } from '@/components/Toast'

const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('')
  const [sentEmail, setSentEmail] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const data = await postForgotPassword({ email })
      setSentEmail((data as any).email ?? email)
    } catch (error) {
      console.error('Ошибка:', error)
      toast('Ошибка отправки')
    }
  }

  if (sentEmail) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4">
        <div className="max-w-md w-full text-center">
          <div className="card p-8 bg-white">
            <Mail className="h-16 w-16 text-blue-600 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Письмо отправлено</h2>
            <p className="text-gray-600 mb-6">
              Ссылка для восстановления пароля отправлена на <span className="font-semibold text-gray-900">{sentEmail}</span>
            </p>
            <Link to="/auth" className="btn-primary inline-block">Вернуться к входу</Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900">Забыли пароль?</h2>
          <p className="mt-2 text-sm text-gray-600">Введите email для восстановления</p>
        </div>
        <div className="card p-8 bg-white">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="input pl-10" placeholder="your@email.com" />
              </div>
            </div>
            <button type="submit" className="w-full btn-primary text-lg py-3">Отправить</button>
          </form>
          <div className="mt-4 text-center">
            <Link to="/auth" className="text-sm text-blue-600 hover:underline">Вернуться к входу</Link>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ForgotPasswordPage
