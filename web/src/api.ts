export interface User {
  id: number
  name: string
  city: string
  gender: string
  goal: string
  age: number
  height_cm: number
  weight_kg: number
  target_cal_per_day: number
  activity_level: string
}

export async function getUsers(): Promise<User[]> {
  const res = await fetch('/api/users')
  if (!res.ok) throw new Error('Не удалось загрузить пользователей')
  return res.json()
}

export async function getReport(name: string, userId?: number): Promise<any> {
  const params = userId !== undefined ? `?user_id=${userId}` : ''
  const res = await fetch(`/api/reports/${name}${params}`)
  if (!res.ok) throw new Error(`Ошибка загрузки отчёта "${name}"`)
  return res.json()
}
