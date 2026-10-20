import { create } from 'zustand';
import { api } from '../services/api';
import { wsManager } from '../services/websocket';
import { useChatStore } from './chatStore';
import { useToastStore } from './toastStore';
import { LoginRequestDTO, RegisterRequestDTO, UserSummaryDTO } from '../types/api';

export interface AuthState {
  token: string | null;
  currentUser: UserSummaryDTO | null;
  activePersonaId: string;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Actions
  initializeSession: () => Promise<void>;
  login: (credentials: LoginRequestDTO) => Promise<void>;
  register: (payload: RegisterRequestDTO) => Promise<void>;
  quickSwitchPersona: (personaId: string) => Promise<void>;
  logout: () => void;
  updateCurrentUserSummary: (summary: Partial<UserSummaryDTO>) => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: localStorage.getItem('pronet_jwt') || sessionStorage.getItem('pronet_jwt'),
  currentUser: null,
  activePersonaId: 'usr_elena_rostova',
  isAuthenticated: false,
  isLoading: true,

  initializeSession: async () => {
    set({ isLoading: true });
    const storedToken = localStorage.getItem('pronet_jwt') || sessionStorage.getItem('pronet_jwt');

    if (storedToken) {
      try {
        const user = await api.auth.getMe();
        set({
          token: storedToken,
          currentUser: user,
          activePersonaId: user.id,
          isAuthenticated: true,
          isLoading: false,
        });
        wsManager.connect(storedToken);
        return;
      } catch (err) {
        console.warn('[Auth] Stored session invalid, falling back to default seed persona:', err);
        localStorage.removeItem('pronet_jwt');
        sessionStorage.removeItem('pronet_jwt');
      }
    }

    // Default seed bootstrap: quick-switch to Elena Rostova
    try {
      const authData = await api.auth.quickSwitch('usr_elena_rostova');
      localStorage.setItem('pronet_jwt', authData.access_token);
      set({
        token: authData.access_token,
        currentUser: authData.user,
        activePersonaId: authData.user.id,
        isAuthenticated: true,
        isLoading: false,
      });
      wsManager.connect(authData.access_token);
    } catch (err) {
      console.warn('[Auth] Could not bootstrap default persona, backend might not be seeded yet:', err);
      set({ isLoading: false, isAuthenticated: false });
    }
  },

  login: async (credentials: LoginRequestDTO) => {
    set({ isLoading: true });
    try {
      const authData = await api.auth.login(credentials);
      localStorage.setItem('pronet_jwt', authData.access_token);
      set({
        token: authData.access_token,
        currentUser: authData.user,
        activePersonaId: authData.user.id,
        isAuthenticated: true,
        isLoading: false,
      });
      wsManager.connect(authData.access_token);
      useToastStore.getState().addToast({
        type: 'success',
        title: 'Signed In',
        message: `Welcome back, ${authData.user.full_name}!`,
      });
    } catch (error: any) {
      set({ isLoading: false });
      throw error;
    }
  },

  register: async (payload: RegisterRequestDTO) => {
    set({ isLoading: true });
    try {
      const authData = await api.auth.register(payload);
      localStorage.setItem('pronet_jwt', authData.access_token);
      set({
        token: authData.access_token,
        currentUser: authData.user,
        activePersonaId: authData.user.id,
        isAuthenticated: true,
        isLoading: false,
      });
      wsManager.connect(authData.access_token);
      useToastStore.getState().addToast({
        type: 'success',
        title: 'Account Created',
        message: `Welcome to ProNet, ${authData.user.full_name}!`,
      });
    } catch (error: any) {
      set({ isLoading: false });
      throw error;
    }
  },

  quickSwitchPersona: async (personaId: string) => {
    const currentActive = get().activePersonaId;
    if (currentActive === personaId && get().isAuthenticated) {
      return;
    }

    try {
      // 1. Dispatch quick-switch
      const authData = await api.auth.quickSwitch(personaId);

      // 2. Persist new JWT
      localStorage.setItem('pronet_jwt', authData.access_token);

      // 3. Gracefully close active WebSocket
      wsManager.disconnect(1000, 'Persona Switched');

      // 4. Reset chat states
      useChatStore.getState().closeActiveChat();
      useChatStore.setState({
        typingPeers: {},
        draftMessages: {},
      });

      // 5. Update auth store
      set({
        token: authData.access_token,
        currentUser: authData.user,
        activePersonaId: authData.user.id,
        isAuthenticated: true,
      });

      // 6. Connect new WebSocket
      wsManager.connect(authData.access_token);

      // 7. Notification toast
      useToastStore.getState().addToast({
        type: 'success',
        title: 'Persona Switched',
        message: `Switched identity to ${authData.user.full_name} (${authData.user.headline.split('|')[0].trim()})`,
      });
    } catch (err: any) {
      useToastStore.getState().addToast({
        type: 'error',
        title: 'Switch Failed',
        message: err.message || 'Failed to switch persona.',
      });
      throw err;
    }
  },

  logout: () => {
    localStorage.removeItem('pronet_jwt');
    sessionStorage.removeItem('pronet_jwt');
    wsManager.disconnect(1000, 'User Logged Out');
    useChatStore.getState().closeActiveChat();
    set({
      token: null,
      currentUser: null,
      activePersonaId: '',
      isAuthenticated: false,
    });
    useToastStore.getState().addToast({
      type: 'info',
      title: 'Logged Out',
      message: 'You have been safely signed out.',
    });
  },

  updateCurrentUserSummary: (summary) => {
    const cur = get().currentUser;
    if (cur) {
      set({ currentUser: { ...cur, ...summary } });
    }
  },
}));
