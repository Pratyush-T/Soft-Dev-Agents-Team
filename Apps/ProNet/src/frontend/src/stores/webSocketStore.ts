import { create } from 'zustand';
import { BadgeCountsDTO } from '../types/api';

export type SocketConnectionStatus = 'CONNECTING' | 'CONNECTED' | 'DISCONNECTED' | 'RECONNECTING';

export interface WebSocketState {
  socket: WebSocket | null;
  status: SocketConnectionStatus;
  onlineUserIds: Set<string>;
  badges: BadgeCountsDTO;
  reconnectAttempts: number;

  // Actions
  setSocket: (socket: WebSocket | null) => void;
  setStatus: (status: SocketConnectionStatus) => void;
  setOnlineUsers: (userIds: string[]) => void;
  updateUserPresence: (userId: string, isOnline: boolean) => void;
  updateBadges: (badges: Partial<BadgeCountsDTO>) => void;
  decrementBadge: (type: keyof BadgeCountsDTO, amount?: number) => void;
  incrementReconnectAttempts: () => void;
  resetReconnectAttempts: () => void;
}

export const useWebSocketStore = create<WebSocketState>((set) => ({
  socket: null,
  status: 'DISCONNECTED',
  onlineUserIds: new Set<string>(),
  badges: {
    unread_messages: 0,
    pending_connections: 0,
    unread_notifications: 0,
  },
  reconnectAttempts: 0,

  setSocket: (socket) => set({ socket }),
  setStatus: (status) => set({ status }),

  setOnlineUsers: (userIds) =>
    set({
      onlineUserIds: new Set<string>(userIds),
    }),

  updateUserPresence: (userId, isOnline) =>
    set((state) => {
      const next = new Set<string>(state.onlineUserIds);
      if (isOnline) {
        next.add(userId);
      } else {
        next.delete(userId);
      }
      return { onlineUserIds: next };
    }),

  updateBadges: (badges) =>
    set((state) => ({
      badges: {
        ...state.badges,
        ...badges,
      },
    })),

  decrementBadge: (type, amount = 1) =>
    set((state) => ({
      badges: {
        ...state.badges,
        [type]: Math.max(0, state.badges[type] - amount),
      },
    })),

  incrementReconnectAttempts: () =>
    set((state) => ({ reconnectAttempts: state.reconnectAttempts + 1 })),

  resetReconnectAttempts: () => set({ reconnectAttempts: 0 }),
}));
