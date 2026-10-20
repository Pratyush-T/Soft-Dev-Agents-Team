import { useWebSocketStore } from '../stores/webSocketStore';
import { useChatStore } from '../stores/chatStore';
import { useToastStore } from '../stores/toastStore';
import { WebSocketClientFrame, WebSocketServerFrame } from '../types/api';

class WebSocketManager {
  private socket: WebSocket | null = null;
  private token: string | null = null;
  private pingInterval: number | null = null;
  private reconnectTimeout: number | null = null;
  private isManuallyClosed = false;

  public connect(token: string) {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      if (this.token === token) {
        return; // already connected with this token
      }
      this.disconnect(1000, 'Reconnecting with new token');
    }

    this.token = token;
    this.isManuallyClosed = false;
    useWebSocketStore.getState().setStatus('CONNECTING');

    // Determine host and protocol
    const isSecure = window.location.protocol === 'https:';
    const wsProto = isSecure ? 'wss:' : 'ws:';
    // If in dev environment with Vite proxy or direct port
    const wsHost = window.location.port === '5173' ? 'localhost:8000' : window.location.host;
    const wsUrl = `${wsProto}//${wsHost}/ws?token=${encodeURIComponent(token)}`;

    try {
      this.socket = new WebSocket(wsUrl);
      useWebSocketStore.getState().setSocket(this.socket);

      this.socket.onopen = () => {
        useWebSocketStore.getState().setStatus('CONNECTED');
        useWebSocketStore.getState().resetReconnectAttempts();
        this.startHeartbeat();
      };

      this.socket.onmessage = (event) => {
        try {
          const frame: WebSocketServerFrame = JSON.parse(event.data);
          this.handleInboundFrame(frame);
        } catch (e) {
          console.error('[WebSocket] Failed to parse frame:', e);
        }
      };

      this.socket.onclose = (event) => {
        this.stopHeartbeat();
        useWebSocketStore.getState().setStatus('DISCONNECTED');
        useWebSocketStore.getState().setSocket(null);

        if (!this.isManuallyClosed && event.code !== 1000 && event.code !== 4001) {
          this.scheduleReconnect();
        }
      };

      this.socket.onerror = (error) => {
        console.error('[WebSocket] Error observed:', error);
      };
    } catch (err) {
      console.error('[WebSocket] Connection failed:', err);
      useWebSocketStore.getState().setStatus('DISCONNECTED');
      this.scheduleReconnect();
    }
  }

  public disconnect(code: number = 1000, reason: string = 'Normal Closure') {
    this.isManuallyClosed = true;
    this.stopHeartbeat();
    if (this.reconnectTimeout) {
      window.clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    if (this.socket) {
      try {
        this.socket.close(code, reason);
      } catch (e) {
        console.warn('[WebSocket] Error closing socket:', e);
      }
      this.socket = null;
      useWebSocketStore.getState().setSocket(null);
    }
    useWebSocketStore.getState().setStatus('DISCONNECTED');
  }

  public sendFrame(frame: WebSocketClientFrame) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(frame));
    } else {
      console.warn('[WebSocket] Cannot send frame, socket is not OPEN');
    }
  }

  public sendMessage(recipientId: string, content: string): string {
    const clientMsgId = `tmp_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`;
    this.sendFrame({
      type: 'SEND_MESSAGE',
      client_msg_id: clientMsgId,
      recipient_id: recipientId,
      content,
    });
    return clientMsgId;
  }

  public sendTyping(recipientId: string, isTyping: boolean) {
    this.sendFrame({
      type: 'TYPING',
      recipient_id: recipientId,
      is_typing: isTyping,
    });
  }

  public sendReadAck(peerId: string, lastMessageId: string) {
    this.sendFrame({
      type: 'READ_ACK',
      conversation_peer_id: peerId,
      last_message_id: lastMessageId,
    });
  }

  private startHeartbeat() {
    this.stopHeartbeat();
    this.pingInterval = window.setInterval(() => {
      this.sendFrame({
        type: 'PING',
        timestamp: new Date().toISOString(),
      });
    }, 30000);
  }

  private stopHeartbeat() {
    if (this.pingInterval) {
      window.clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  private scheduleReconnect() {
    const attempts = useWebSocketStore.getState().reconnectAttempts;
    if (attempts >= 10) {
      console.warn('[WebSocket] Max reconnect attempts exceeded.');
      return;
    }

    useWebSocketStore.getState().incrementReconnectAttempts();
    useWebSocketStore.getState().setStatus('RECONNECTING');

    const delay = Math.min(1000 * Math.pow(2, attempts), 30000);
    this.reconnectTimeout = window.setTimeout(() => {
      if (this.token && !this.isManuallyClosed) {
        this.connect(this.token);
      }
    }, delay);
  }

  private handleInboundFrame(frame: WebSocketServerFrame) {
    const wsStore = useWebSocketStore.getState();
    const chatStore = useChatStore.getState();
    const toastStore = useToastStore.getState();

    switch (frame.type) {
      case 'CONNECTED':
        if (frame.online_connection_ids) {
          wsStore.setOnlineUsers(frame.online_connection_ids);
        }
        if (frame.badges) {
          wsStore.updateBadges(frame.badges);
        }
        break;

      case 'PONG':
        // Heartbeat ACK received
        break;

      case 'PRESENCE_UPDATE':
        wsStore.updateUserPresence(frame.user_id, frame.is_online);
        break;

      case 'BADGE_UPDATE':
        wsStore.updateBadges(frame.badges);
        break;

      case 'NEW_MESSAGE':
        const peerId = frame.message.is_outgoing ? frame.message.recipient_id : frame.message.sender_id;
        chatStore.appendMessage(peerId, frame.message);

        // If not in active chat with peer, show notification & increment badge
        if (chatStore.activePeerId !== peerId && !frame.message.is_outgoing) {
          wsStore.updateBadges({
            unread_messages: wsStore.badges.unread_messages + 1,
          });
          toastStore.addToast({
            type: 'info',
            title: 'New Message',
            message: frame.message.content.length > 50 ? frame.message.content.substring(0, 50) + '...' : frame.message.content,
          });
        }
        break;

      case 'MESSAGE_ACK':
        // Status confirmation for outgoing message
        break;

      case 'TYPING':
        chatStore.setPeerTyping(frame.sender_id, frame.is_typing);
        break;

      case 'READ_ACK':
        // Peer has read messages up to read_at
        break;

      case 'NOTIFICATION':
        wsStore.updateBadges({
          unread_notifications: wsStore.badges.unread_notifications + 1,
        });
        toastStore.addToast({
          type: 'info',
          title: frame.notification.title,
          message: frame.notification.content,
        });
        break;

      case 'ERROR':
        toastStore.addToast({
          type: 'error',
          title: 'WebSocket Error',
          message: frame.message,
        });
        break;

      default:
        break;
    }
  }
}

export const wsManager = new WebSocketManager();
