import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api } from '../lib/api';

interface User {
  id: string;
  email: string;
  full_name: string;
}

interface RegistrationResult {
  requiresConfirmation: boolean;
  message: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, full_name: string) => Promise<RegistrationResult>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadUser = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const userData = await api.get('/auth/me');
          setUser(userData);
        } catch (error) {
          localStorage.removeItem('token');
        }
      }
      setLoading(false);
    };
    loadUser();
  }, []);

  const login = async (email: string, password: string) => {
    const data = await api.post('/auth/login', { email, password });
    localStorage.setItem('token', data.access_token);
    const userData = await api.get('/auth/me');
    setUser(userData);
  };

  const register = async (email: string, password: string, full_name: string) => {
    const data = await api.post('/auth/register', { email, password, full_name });
    
    // Check if email confirmation is required
    if (data.requires_confirmation) {
      return { requiresConfirmation: true, message: data.message };
    }
    
    // Auto-login if confirmation not required
    if (data.access_token) {
      localStorage.setItem('token', data.access_token);
      const userData = await api.get('/auth/me');
      setUser(userData);
    }
    
    return { requiresConfirmation: false, message: data.message };
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

