import React, { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { NotificationDTO } from '../../types/api';
import { useWebSocketStore } from '../../stores/webSocketStore';
import { useToastStore } from '../../stores/toastStore';
import { Avatar } from '../../components/ui/Avatar';
import { Skeleton } from '../../components/ui/Skeleton';
import { Bell, CheckCheck, RefreshCw, X, AlertTriangle } from 'lucide-react';

export interface NotificationsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigate?: (tab: string, id?: string) => void;
}

export const NotificationsDrawer: React.FC<NotificationsDrawerProps> = ({
  isOpen,
  onClose,
  onNavigate,
}) => {
  const [notifications, setNotifications] = useState<NotificationDTO[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { updateBadges } = useWebSocketStore();
  const { addToast } = useToastStore();

  const fetchNotifications = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.notifications.getNotifications();
      setNotifications(data.items);
    } catch (err: any) {
      setError(err.message || 'Failed to load notifications');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchNotifications();
    }
  }, [isOpen]);

  const handleMarkAllRead = async () => {
    try {
      await api.notifications.markRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      updateBadges({ unread_notifications: 0 });
      addToast({
        type: 'success',
        title: 'All Caught Up',
        message: 'Marked all notifications as read',
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Failed',
        message: err.message || 'Could not mark notifications as read',
      });
    }
  };

  if (!isOpen) return null;

  return (
    <div className="absolute right-0 mt-2 w-96 max-w-[calc(100vw-2rem)] bg-white border border-surface-200 rounded-xl shadow-elevation-3 z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-100">
      {/* Header */}
      <div className="flex items-center justify-between p-3.5 bg-surface-50 border-b border-surface-200">
        <div className="flex items-center gap-2">
          <Bell className="w-4 h-4 text-brand-600" />
          <h3 className="text-sm font-bold text-surface-900">Notifications</h3>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleMarkAllRead}
            className="flex items-center gap-1 text-xs text-brand-600 hover:text-brand-700 font-medium transition-colors"
            title="Mark all as read"
          >
            <CheckCheck className="w-3.5 h-3.5" />
            Mark all read
          </button>
          <button
            onClick={onClose}
            className="p-1 text-surface-400 hover:text-surface-700 rounded transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="max-h-96 overflow-y-auto divide-y divide-surface-100">
        {/* 1. Loading Skeleton */}
        {loading && (
          <div className="p-3 space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="flex gap-3 items-start">
                <Skeleton variant="circular" width={36} height={36} />
                <div className="flex-1 space-y-1.5">
                  <Skeleton width="60%" height={12} />
                  <Skeleton width="90%" height={10} />
                  <Skeleton width="30%" height={8} />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 2. Error State with Retry */}
        {!loading && error && (
          <div className="p-6 text-center">
            <AlertTriangle className="w-8 h-8 text-warning-500 mx-auto mb-2" />
            <p className="text-xs text-surface-700 font-medium">{error}</p>
            <button
              onClick={fetchNotifications}
              className="mt-3 inline-flex items-center gap-1.5 text-xs text-brand-600 font-medium hover:underline"
            >
              <RefreshCw className="w-3 h-3" /> Retry Loading
            </button>
          </div>
        )}

        {/* 3. Empty State */}
        {!loading && !error && notifications.length === 0 && (
          <div className="p-8 text-center">
            <div className="w-10 h-10 rounded-full bg-surface-100 flex items-center justify-center mx-auto mb-2 text-surface-400">
              <Bell className="w-5 h-5" />
            </div>
            <h4 className="text-xs font-bold text-surface-800">No Notifications Yet</h4>
            <p className="text-[11px] text-surface-500 mt-0.5">
              Updates on post reactions, comments, connections, and applications will appear here.
            </p>
          </div>
        )}

        {/* 4. Populated State */}
        {!loading &&
          !error &&
          notifications.map((item) => (
            <div
              key={item.id}
              onClick={() => {
                if (item.reference_type === 'POST') onNavigate?.('feed');
                if (item.reference_type === 'CONNECTION') onNavigate?.('network');
                if (item.reference_type === 'JOB') onNavigate?.('jobs');
                onClose();
              }}
              className={`p-3 flex items-start gap-3 hover:bg-surface-50 transition-colors cursor-pointer ${
                !item.is_read ? 'bg-brand-50/40' : ''
              }`}
            >
              <Avatar src={item.actor.avatar_url} alt={item.actor.full_name} size="sm" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-1">
                  <span className="text-xs font-semibold text-surface-900 truncate">
                    {item.title}
                  </span>
                  {!item.is_read && <span className="w-2 h-2 rounded-full bg-brand-600 shrink-0" />}
                </div>
                <p className="text-[11px] text-surface-600 mt-0.5 line-clamp-2">{item.content}</p>
                <span className="text-[10px] text-surface-400 mt-1 block">
                  {new Date(item.created_at).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </span>
              </div>
            </div>
          ))}
      </div>
    </div>
  );
};
