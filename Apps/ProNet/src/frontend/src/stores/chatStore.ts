import { create } from 'zustand';
import { ConversationSummaryDTO, MessageDTO, UserSummaryDTO } from '../types/api';

export interface ChatState {
  isDockOpen: boolean;
  activePeerId: string | null;
  activePeer: UserSummaryDTO | null;
  conversations: ConversationSummaryDTO[];
  messageHistories: Record<string, MessageDTO[]>;
  typingPeers: Record<string, boolean>;
  draftMessages: Record<string, string>;

  // Actions
  setDockOpen: (isOpen: boolean) => void;
  openChatWithPeer: (peer: UserSummaryDTO) => void;
  closeActiveChat: () => void;
  setConversations: (conversations: ConversationSummaryDTO[]) => void;
  setMessageHistory: (peerId: string, messages: MessageDTO[]) => void;
  appendMessage: (peerId: string, message: MessageDTO) => void;
  setPeerTyping: (peerId: string, isTyping: boolean) => void;
  setDraftMessage: (peerId: string, text: string) => void;
  markConversationReadLocally: (peerId: string) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  isDockOpen: false,
  activePeerId: null,
  activePeer: null,
  conversations: [],
  messageHistories: {},
  typingPeers: {},
  draftMessages: {},

  setDockOpen: (isOpen) => set({ isDockOpen: isOpen }),

  openChatWithPeer: (peer) =>
    set((state) => ({
      isDockOpen: true,
      activePeerId: peer.id,
      activePeer: peer,
      conversations: state.conversations.map((c) =>
        c.peer.id === peer.id ? { ...c, unread_count: 0 } : c
      ),
    })),

  closeActiveChat: () =>
    set({
      activePeerId: null,
      activePeer: null,
    }),

  setConversations: (conversations) => set({ conversations }),

  setMessageHistory: (peerId, messages) =>
    set((state) => ({
      messageHistories: {
        ...state.messageHistories,
        [peerId]: messages,
      },
    })),

  appendMessage: (peerId, message) =>
    set((state) => {
      const existing = state.messageHistories[peerId] || [];
      // deduplicate by message.id
      if (existing.some((m) => m.id === message.id)) {
        return state;
      }
      const updatedHistory = [...existing, message];

      // Update conversations list as well
      const convIndex = state.conversations.findIndex((c) => c.peer.id === peerId);
      let updatedConversations = [...state.conversations];
      if (convIndex >= 0) {
        const conv = updatedConversations[convIndex];
        const isCurrentActive = state.activePeerId === peerId;
        updatedConversations[convIndex] = {
          ...conv,
          last_message: message,
          unread_count: isCurrentActive ? 0 : conv.unread_count + (message.is_outgoing ? 0 : 1),
        };
      }

      return {
        messageHistories: {
          ...state.messageHistories,
          [peerId]: updatedHistory,
        },
        conversations: updatedConversations,
      };
    }),

  setPeerTyping: (peerId, isTyping) =>
    set((state) => ({
      typingPeers: {
        ...state.typingPeers,
        [peerId]: isTyping,
      },
    })),

  setDraftMessage: (peerId, text) =>
    set((state) => ({
      draftMessages: {
        ...state.draftMessages,
        [peerId]: text,
      },
    })),

  markConversationReadLocally: (peerId) =>
    set((state) => ({
      conversations: state.conversations.map((c) =>
        c.peer.id === peerId ? { ...c, unread_count: 0 } : c
      ),
    })),
}));
