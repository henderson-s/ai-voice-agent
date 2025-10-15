import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import type { User, AuthResponse, LoginCredentials, RegisterCredentials } from '../types';
import { api } from '../lib/api';

interface RegistrationResult {
  requiresConfirmation: boolean;
  message: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<RegistrationResult>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadUser = async (): Promise<void> => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const userData = await api.get<User>('/auth/me');
          setUser(userData);
        } catch (error) {
          console.error('Failed to load user:', error);
          localStorage.removeItem('token');
        }
      }
      setLoading(false);
    };
    loadUser();
  }, []);

  const login = async (email: string, password: string): Promise<void> => {
    const credentials: LoginCredentials = { email, password };
    const data = await api.post<AuthResponse>('/auth/login', credentials);
    localStorage.setItem('token', data.access_token);
    const userData = await api.get<User>('/auth/me');
    setUser(userData);
  };

  const register = async (
    email: string,
    password: string,
    _fullName?: string
  ): Promise<RegistrationResult> => {
    const credentials: RegisterCredentials = { email, password };
    const data = await api.post<any>('/auth/register', credentials);

    // Check if email confirmation is required
    if (data.requires_confirmation) {
      return {
        requiresConfirmation: true,
        message: data.message || 'Please check your email to confirm your account',
      };
    }

    // Auto-login if confirmation not required
    if (data.access_token) {
      localStorage.setItem('token', data.access_token);
      const userData = await api.get<User>('/auth/me');
      setUser(userData);
    }

    return {
      requiresConfirmation: false,
      message: data.message || 'Account created successfully',
    };
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};

