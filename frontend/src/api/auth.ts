import apiClient from './client'
import type { AuthUser } from '../stores/authStore'

export interface LoginResponse {
  access_token: string
  token_type: string
  user_id: string
  username: string
  role_type: string
  is_first_login: number
}

/** 后端包装层：{ success, code, message, data: LoginResponse } */
interface WrappedLoginResponse {
  success: boolean
  code: number
  message: string
  data: LoginResponse
}

/**
 * 兼容新旧两种响应格式：
 * - 新格式：{ success: true, data: { access_token, ... } }
 * - 旧格式（万一退化）：{ access_token, ... }
 */
function mapResponse(raw: LoginResponse | WrappedLoginResponse): { token: string; user: AuthUser } {
  const data: LoginResponse = 'data' in raw && raw.data ? raw.data : raw as LoginResponse
  return {
    token: data.access_token,
    user: {
      userId: data.user_id,
      username: data.username,
      roleType: data.role_type,
      isFirstLogin: data.is_first_login,
    },
  }
}

export const authApi = {
  async register(params: {
    username: string
    password: string
    email?: string
    role_type?: string
  }): Promise<{ token: string; user: AuthUser }> {
    const { data } = await apiClient.post<WrappedLoginResponse>('/api/v1/auth/register', params)
    return mapResponse(data)
  },

  async login(params: {
    username: string
    password: string
  }): Promise<{ token: string; user: AuthUser }> {
    const { data } = await apiClient.post<WrappedLoginResponse>('/api/v1/auth/login', params)
    return mapResponse(data)
  },

  async sendOtp(phone: string): Promise<{ demo_code?: string; expire_seconds: number }> {
    const { data } = await apiClient.post('/api/v1/auth/send-otp', { phone })
    return data
  },

  async verifyOtp(phone: string, code: string): Promise<{ token: string; user: AuthUser }> {
    const { data } = await apiClient.post<WrappedLoginResponse>('/api/v1/auth/verify-otp', { phone, code })
    return mapResponse(data)
  },

  async guestLogin(): Promise<{ token: string; user: AuthUser }> {
    const { data } = await apiClient.post<WrappedLoginResponse>('/api/v1/auth/guest')
    return mapResponse(data)
  },

  async updateProfile(
    userId: string,
    params: { role_type?: string; meta_json?: Record<string, unknown>; is_first_login?: number },
  ): Promise<void> {
    await apiClient.post('/api/v1/auth/update-profile', params, { params: { user_id: userId } })
  },

  async getUserInfo(userId: string): Promise<{
    user_id: string
    username: string
    email: string
    phone: string
    role_type: string
    onboarded: boolean
    create_time: string
    meta_json: Record<string, unknown>
  }> {
    const { data } = await apiClient.get(`/api/v1/auth/user/${userId}`)
    return data
  },

  async changePassword(params: {
    user_id: string
    old_password: string
    new_password: string
  }): Promise<void> {
    await apiClient.post('/api/v1/auth/change-password', params)
  },
}
