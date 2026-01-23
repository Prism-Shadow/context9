import api from './api';
import type {
  LoginRequest,
  LoginResponse,
  Admin,
  ChangePasswordRequest,
} from '../utils/types';

// 管理员登录
export const login = async (data: LoginRequest): Promise<LoginResponse> => {
  const response = await api.post<LoginResponse>('/api/admin/login', data);
  return response.data;
};

// 获取当前管理员信息
export const getCurrentAdmin = async (): Promise<Admin> => {
  const response = await api.get<Admin>('/api/admin/me');
  return response.data;
};

// 登出
export const logout = async (): Promise<void> => {
  await api.post('/api/admin/logout');
};

// 修改密码
export const changePassword = async (
  data: ChangePasswordRequest
): Promise<{ message: string }> => {
  const response = await api.post<{ message: string }>(
    '/api/admin/change-password',
    data
  );
  return response.data;
};
