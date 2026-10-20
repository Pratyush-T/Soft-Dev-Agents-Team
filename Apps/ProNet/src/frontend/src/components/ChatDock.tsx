import React, { useState, useEffect, useRef } from 'react';
import { useChatStore } from '../stores/chatStore';
import { useWebSocketStore } from '../stores/webSocketStore';
import { useAuthStore } from '../stores/authStore';
import { wsManager } from '../services/websocket';
import { api } from '../services/api';
import { Avatar } from './ui/Avatar';
import { Skeleton } from './ui/Skeleton';
import { MessageDTO } from '../types/api';
import {
  MessageSquare,
  ChevronDown,
  ChevronUp,
  X,
  ArrowLeft,
  Send,
  Search,
  CheckCheck,
} from 'lucide-react';

export const ChatDock: React.FC = () => {
  const {
    isDockOpen,
    setDockOpen,
    activePeer,
    activePeerId,
    openChatWithPeer,
    closeActiveChat,
    conversations,
    setConversations,
    messageHistories,
    setMessageHistory,
    appendMessage,
    typingPeers,
    markConversationReadLocally,
  } = useChatStore();

  const { onlineUserIds, badges, decrementBadge } = useWebSocketStore();
  const { currentUser } = useAuthStore();

  const [inputMessage, setInputMessage] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [loadingConvs, setLoadingConvs] = useState(false);
  const [isTypingSent, setIsTypingSent] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const typingTimeoutRef = useRef<number | null>(null);

  // Auto-scroll to bottom of messages
  const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
    messagesEndRef.current?.scrollIntoView({ behavior });
  };

  // Load conversations when dock is open and no active peer
  useEffect(() => {
    if (isDockOpen && !activePeerId && currentUser) {
      setLoadingConvs(true);
      api.messages
        .getConversations()
        .then((data) => {
          setConversations(data);
        })
        .catch((e) => {
          console.warn('[ChatDock] Failed to fetch conversations:', e);
        })
        .finally(() => {
          setLoadingConvs(false);
        });
    }
  }, [isDockOpen, activePeerId, currentUser, setConversations]);

  // Load message history when active peer changes
  useEffect(() => {
    if (activePeerId && currentUser) {
      setLoadingHistory(true);
      api.messages
        .getMessages(activePeerId)
        .then((res) => {
          setMessageHistory(activePeerId, res.items);
          markConversationReadLocally(activePeerId);
          api.messages.markRead(activePeerId).catch(() => {});
          if (badges.unread_messages > 0) {
            decrementBadge('unread_messages', 1);
          }
          setTimeout(() => scrollToBottom('auto'), 50);
        })
        .catch((e) => {
          console.warn('[ChatDock] Failed to load messages:', e);
        })
        .finally(() => {
          setLoadingHistory(false);
        });
    }
  }, [activePeerId, currentUser, setMessageHistory, markConversationReadLocally, decrementBadge, badges.unread_messages]);

  // Scroll to bottom when message history updates
  const activeMessages = activePeerId ? messageHistories[activePeerId] || [] : [];
  useEffect(() => {
    if (activePeerId && activeMessages.length > 0) {
      scrollToBottom('smooth');
    }
  }, [activeMessages.length, activePeerId]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputMessage(e.target.value);

    if (activePeerId) {
      if (!isTypingSent) {
        setIsTypingSent(true);
        wsManager.sendTyping(activePeerId, true);
      }

      if (typingTimeoutRef.current) {
        window.clearTimeout(typingTimeoutRef.current);
      }

      typingTimeoutRef.current = window.setTimeout(() => {
        wsManager.sendTyping(activePeerId, false);
        setIsTypingSent(false);
      }, 2000);
    }
  };

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    const text = inputMessage.trim();
    if (!text || !activePeerId || !currentUser) return;

    // Send via WebSocket
    wsManager.sendMessage(activePeerId, text);
    wsManager.sendTyping(activePeerId, false);
    setIsTypingSent(false);

    // Optimistically append outgoing message
    const outgoingMsg: MessageDTO = {
      id: `tmp_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      sender_id: currentUser.id,
      recipient_id: activePeerId,
      content: text,
      read_at: null,
      created_at: new Date().toISOString(),
      is_outgoing: true,
    };
    appendMessage(activePeerId, outgoingMsg);

    setInputMessage('');
    setTimeout(() => scrollToBottom('smooth'), 20);
  };

  const isPeerOnline = activePeerId ? onlineUserIds.has(activePeerId) : false;
  const isPeerTyping = activePeerId ? !!typingPeers[activePeerId] : false;

  const filteredConversations = conversations.filter((c) =>
    c.peer.full_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatMessageTime = (isoString: string) => {
    const d = new Date(isoString);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // If dock is closed, render compact button badge
  if (!isDockOpen) {
    return (
      <div className="fixed bottom-0 right-6 z-40">
        <button
          onClick={() => setDockOpen(true)}
          className="flex items-center gap-2.5 px-4 py-2.5 bg-white border border-surface-200 border-b-0 rounded-t-xl shadow-elevation-float hover:bg-surface-50 transition-all font-semibold text-xs text-surface-900 group"
          aria-label="Open Messaging Dock"
        >
          <div className="relative">
            <MessageSquare className="w-4 h-4 text-brand-600" />
            {badges.unread_messages > 0 && (
              <span className="absolute -top-1 -right-2 bg-danger-600 text-white text-[9px] font-bold px-1 rounded-full min-w-[14px] text-center">
                {badges.unread_messages > 9 ? '9+' : badges.unread_messages}
              </span>
            )}
          </div>
          <span>Messaging</span>
          <ChevronUp className="w-4 h-4 text-surface-400 group-hover:text-surface-700 transition-colors" />
        </button>
      </div>
    );
  }

  // Expanded Dock
  return (
    <div
      className="fixed bottom-0 right-6 z-40 w-80 sm:w-96 h-[460px] bg-white border border-surface-200 border-b-0 rounded-t-xl shadow-elevation-float flex flex-col overflow-hidden animate-in slide-in-from-bottom-5 duration-150"
      role="region"
      aria-label="Direct Messaging"
    >
      {/* Header */}
      <div className="h-12 bg-white border-b border-surface-200 px-3 flex items-center justify-between shrink-0 shadow-sm">
        {activePeer ? (
          <div className="flex items-center gap-2 min-w-0">
            <button
              onClick={closeActiveChat}
              className="p-1 text-surface-500 hover:text-surface-900 rounded-md transition-colors"
              title="Back to conversation list"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <Avatar
              src={activePeer.avatar_url}
              alt={activePeer.full_name}
              size="xs"
              isOnline={isPeerOnline}
            />
            <div className="min-w-0">
              <div className="text-xs font-bold text-surface-900 truncate">
                {activePeer.full_name}
              </div>
              <div className="text-[10px] text-surface-500 truncate">
                {isPeerTyping ? (
                  <span className="text-brand-600 font-semibold italic">typing...</span>
                ) : isPeerOnline ? (
                  <span className="text-emerald-600 font-medium">Online</span>
                ) : (
                  'Offline'
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-brand-600" />
            <span className="text-xs font-bold text-surface-900">Messaging</span>
            {badges.unread_messages > 0 && (
              <span className="bg-danger-600 text-white text-[10px] font-bold px-1.5 py-0.2 rounded-full">
                {badges.unread_messages}
              </span>
            )}
          </div>
        )}

        <div className="flex items-center gap-1">
          <button
            onClick={() => setDockOpen(false)}
            className="p-1 text-surface-400 hover:text-surface-700 rounded-md transition-colors"
            title="Minimize messaging"
          >
            <ChevronDown className="w-4 h-4" />
          </button>
          <button
            onClick={() => {
              closeActiveChat();
              setDockOpen(false);
            }}
            className="p-1 text-surface-400 hover:text-surface-700 rounded-md transition-colors"
            title="Close dock"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Body */}
      {activePeer ? (
        /* Active Chat Thread */
        <div className="flex-1 flex flex-col min-h-0 bg-surface-50/50">
          {/* Messages Stream */}
          <div className="flex-1 overflow-y-auto p-3 space-y-3 text-xs">
            {loadingHistory && (
              <div className="space-y-3 py-2">
                <Skeleton width="60%" height={32} className="rounded-xl ml-auto" />
                <Skeleton width="55%" height={32} className="rounded-xl" />
                <Skeleton width="70%" height={32} className="rounded-xl ml-auto" />
              </div>
            )}

            {!loadingHistory && activeMessages.length === 0 && (
              <div className="text-center py-10 px-4 space-y-2">
                <Avatar
                  src={activePeer.avatar_url}
                  alt={activePeer.full_name}
                  size="lg"
                  className="mx-auto"
                />
                <h4 className="text-xs font-bold text-surface-900">
                  {activePeer.full_name}
                </h4>
                <p className="text-[11px] text-surface-500 line-clamp-2">
                  {activePeer.headline}
                </p>
                <div className="p-3 bg-white border border-surface-200 rounded-lg text-[11px] text-surface-600 leading-relaxed shadow-sm">
                  This is the start of your direct conversation with {activePeer.full_name}. Direct messages are delivered in real-time over WebSocket.
                </div>
              </div>
            )}

            {!loadingHistory &&
              activeMessages.map((msg) => {
                const isMine = msg.is_outgoing || (currentUser && msg.sender_id === currentUser.id);
                return (
                  <div
                    key={msg.id}
                    className={`flex flex-col ${isMine ? 'items-end' : 'items-start'}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-2xl px-3.5 py-2 text-xs leading-relaxed break-words shadow-sm ${
                        isMine
                          ? 'bg-brand-600 text-white rounded-br-none'
                          : 'bg-white text-surface-900 border border-surface-200 rounded-bl-none'
                      }`}
                    >
                      {msg.content}
                    </div>
                    <div className="flex items-center gap-1 mt-0.5 px-1 text-[10px] text-surface-400">
                      <span>{formatMessageTime(msg.created_at)}</span>
                      {isMine && <CheckCheck className="w-3 h-3 text-brand-500" />}
                    </div>
                  </div>
                );
              })}

            {isPeerTyping && (
              <div className="flex items-center gap-1.5 text-xs text-surface-500 italic py-1">
                <span className="w-1.5 h-1.5 rounded-full bg-brand-600 animate-bounce" />
                <span className="w-1.5 h-1.5 rounded-full bg-brand-600 animate-bounce [animation-delay:0.2s]" />
                <span className="w-1.5 h-1.5 rounded-full bg-brand-600 animate-bounce [animation-delay:0.4s]" />
                <span className="text-[11px] ml-1">{activePeer.full_name} is typing...</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Chat Input */}
          <form
            onSubmit={handleSendMessage}
            className="p-2 bg-white border-t border-surface-200 flex items-center gap-2 shrink-0"
          >
            <input
              type="text"
              placeholder={`Message ${activePeer.full_name.split(' ')[0]}...`}
              value={inputMessage}
              onChange={handleInputChange}
              className="flex-1 text-xs rounded-lg border border-surface-200 bg-surface-50 px-3 py-2 text-surface-900 focus:outline-none focus:border-brand-600 focus:bg-white"
            />
            <button
              type="submit"
              disabled={!inputMessage.trim()}
              className="p-2 rounded-lg bg-brand-600 text-white hover:bg-brand-700 disabled:opacity-40 transition-colors shadow-sm"
              title="Send message"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      ) : (
        /* Conversations List */
        <div className="flex-1 flex flex-col min-h-0">
          {/* Search Bar */}
          <div className="p-2 border-b border-surface-100">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-surface-400 absolute left-2.5 top-2.5" />
              <input
                type="text"
                placeholder="Search conversations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 text-xs rounded-md border border-surface-200 bg-surface-50 focus:outline-none focus:border-brand-600"
              />
            </div>
          </div>

          {/* Conversation List Stream */}
          <div className="flex-1 overflow-y-auto divide-y divide-surface-100">
            {loadingConvs && (
              <div className="p-3 space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="flex items-center gap-2.5">
                    <Skeleton variant="circular" width={36} height={36} />
                    <div className="flex-1 space-y-1.5">
                      <Skeleton width="50%" height={12} />
                      <Skeleton width="80%" height={10} />
                    </div>
                  </div>
                ))}
              </div>
            )}

            {!loadingConvs && filteredConversations.length === 0 && (
              <div className="p-6 text-center text-xs text-surface-500 space-y-2">
                <p className="font-semibold text-surface-800">No Conversations Yet</p>
                <p className="text-[11px] text-surface-500 leading-relaxed">
                  Direct messages can be sent to any confirmed 1st-degree connection. Visit a profile or network connection to start a chat!
                </p>
              </div>
            )}

            {!loadingConvs &&
              filteredConversations.map((c) => {
                const isOnline = onlineUserIds.has(c.peer.id);
                return (
                  <button
                    key={c.peer.id}
                    onClick={() => openChatWithPeer(c.peer)}
                    className="w-full text-left p-3 hover:bg-surface-50 flex items-start gap-2.5 transition-colors group"
                  >
                    <Avatar
                      src={c.peer.avatar_url}
                      alt={c.peer.full_name}
                      size="sm"
                      isOnline={isOnline}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-surface-900 group-hover:text-brand-600 truncate">
                          {c.peer.full_name}
                        </span>
                        {c.last_message && (
                          <span className="text-[10px] text-surface-400">
                            {formatMessageTime(c.last_message.created_at)}
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-surface-500 line-clamp-1 mt-0.5">
                        {c.last_message?.content || c.peer.headline}
                      </p>
                    </div>
                    {c.unread_count > 0 && (
                      <span className="bg-brand-600 text-white text-[10px] font-bold px-1.5 py-0.2 rounded-full shrink-0">
                        {c.unread_count}
                      </span>
                    )}
                  </button>
                );
              })}
          </div>
        </div>
      )}
    </div>
  );
};
