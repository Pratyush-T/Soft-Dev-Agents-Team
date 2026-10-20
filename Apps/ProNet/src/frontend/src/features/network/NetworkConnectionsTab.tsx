import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { ConnectionDTO } from '../../types/api';
import { useChatStore } from '../../stores/chatStore';
import { useWebSocketStore } from '../../stores/webSocketStore';
import { useToastStore } from '../../stores/toastStore';
import { Avatar } from '../../components/ui/Avatar';
import { Button } from '../../components/ui/Button';
import { Skeleton } from '../../components/ui/Skeleton';
import { DegreeBadge } from '../../components/ui/DegreeBadge';
import {
  Search,
  MessageSquare,
  UserX,
  Users,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react';

export interface NetworkConnectionsTabProps {
  onSelectUser?: (userId: string) => void;
  onDiscoverPeers?: () => void;
}

export const NetworkConnectionsTab: React.FC<NetworkConnectionsTabProps> = ({
  onSelectUser,
  onDiscoverPeers,
}) => {
  const [connections, setConnections] = useState<ConnectionDTO[]>([]);
  const [filterQuery, setFilterQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { openChatWithPeer } = useChatStore();
  const { onlineUserIds } = useWebSocketStore();
  const { addToast } = useToastStore();

  const fetchConnections = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.connections.getConnections();
      setConnections(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load professional connections.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConnections();
  }, []);

  const handleDisconnect = async (userId: string, name: string) => {
    if (!window.confirm(`Disconnect from ${name}? Direct messaging will be disabled.`)) return;

    try {
      await api.connections.disconnect(userId);
      setConnections((prev) => prev.filter((c) => c.peer.id !== userId));
      addToast({
        type: 'info',
        title: 'Connection Removed',
        message: `Removed ${name} from your 1st-degree connections.`,
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Disconnect Failed',
        message: err.message || 'Could not disconnect.',
      });
    }
  };

  const filteredConnections = connections.filter(
    (c) =>
      c.peer.full_name.toLowerCase().includes(filterQuery.toLowerCase()) ||
      c.peer.headline.toLowerCase().includes(filterQuery.toLowerCase())
  );

  return (
    <div className="space-y-4">
      {/* Search Filter Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white p-3.5 rounded-xl border border-surface-200">
        <div className="text-sm font-bold text-surface-900">
          {connections.length} Confirmed Connection{connections.length === 1 ? '' : 's'}
        </div>
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-surface-400 absolute left-2.5 top-2.5 pointer-events-none" />
          <input
            type="text"
            placeholder="Search connections by name or role..."
            value={filterQuery}
            onChange={(e) => setFilterQuery(e.target.value)}
            className="w-full text-xs rounded-md border border-surface-200 bg-surface-50 pl-8 pr-3 py-1.5 focus:outline-none focus:border-brand-600 focus:bg-white"
          />
        </div>
      </div>

      {/* 1. Loading Skeleton */}
      {loading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="bg-white p-4 rounded-xl border border-surface-200 text-center space-y-3">
              <Skeleton variant="circular" width={64} height={64} className="mx-auto" />
              <Skeleton width="60%" height={14} className="mx-auto" />
              <Skeleton width="80%" height={10} className="mx-auto" />
              <Skeleton width="100%" height={32} />
            </div>
          ))}
        </div>
      )}

      {/* 2. Error State with Retry */}
      {!loading && error && (
        <div className="bg-white p-8 rounded-xl border border-danger-200 text-center space-y-3">
          <AlertTriangle className="w-8 h-8 text-danger-500 mx-auto" />
          <h4 className="text-sm font-bold text-surface-900">Failed to Load Connections</h4>
          <p className="text-xs text-surface-600">{error}</p>
          <Button
            variant="primary"
            size="sm"
            onClick={fetchConnections}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Refresh Network
          </Button>
        </div>
      )}

      {/* 3. Empty State with CTA */}
      {!loading && !error && connections.length === 0 && (
        <div className="bg-white p-12 rounded-xl border border-surface-200 text-center space-y-3">
          <div className="w-14 h-14 bg-surface-100 rounded-full flex items-center justify-center mx-auto text-surface-400">
            <Users className="w-7 h-7" />
          </div>
          <h4 className="text-base font-bold text-surface-900">
            You Have No 1st-Degree Connections Yet
          </h4>
          <p className="text-xs text-surface-500 max-w-sm mx-auto">
            Expand your professional network by sending connection requests from user profiles or recommended peers.
          </p>
          {onDiscoverPeers && (
            <Button variant="primary" size="sm" onClick={onDiscoverPeers}>
              Discover Professionals
            </Button>
          )}
        </div>
      )}

      {/* 4. Populated Grid View */}
      {!loading && !error && connections.length > 0 && (
        <>
          {filteredConnections.length === 0 ? (
            <div className="bg-white p-8 rounded-xl border border-surface-200 text-center text-xs text-surface-500">
              No connections found matching &quot;{filterQuery}&quot;.
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {filteredConnections.map((conn) => {
                const isOnline = onlineUserIds.has(conn.peer.id);

                return (
                  <div
                    key={conn.id}
                    className="bg-white rounded-xl border border-surface-200 shadow-elevation-1 p-4 flex flex-col items-center text-center hover:shadow-elevation-2 transition-shadow relative group"
                  >
                    {/* Disconnect top-right button */}
                    <button
                      onClick={() => handleDisconnect(conn.peer.id, conn.peer.full_name)}
                      className="absolute top-2.5 right-2.5 p-1 text-surface-400 hover:text-danger-600 rounded transition-colors opacity-0 group-hover:opacity-100"
                      title="Remove Connection"
                    >
                      <UserX className="w-4 h-4" />
                    </button>

                    <div
                      onClick={() => onSelectUser?.(conn.peer.id)}
                      className="cursor-pointer mb-2"
                    >
                      <Avatar
                        src={conn.peer.avatar_url}
                        alt={conn.peer.full_name}
                        size="lg"
                        isOnline={isOnline}
                      />
                    </div>

                    <button
                      onClick={() => onSelectUser?.(conn.peer.id)}
                      className="text-xs font-bold text-surface-900 hover:text-brand-600 transition-colors line-clamp-1"
                    >
                      {conn.peer.full_name}
                    </button>

                    <div className="my-1">
                      <DegreeBadge degree="1st" />
                    </div>

                    <p className="text-[11px] text-surface-500 line-clamp-2 min-h-[32px] px-1">
                      {conn.peer.headline}
                    </p>

                    <span className="text-[10px] text-surface-400 mt-2 mb-3">
                      Connected {new Date(conn.created_at).toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' })}
                    </span>

                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full mt-auto"
                      onClick={() => openChatWithPeer(conn.peer)}
                      leftIcon={<MessageSquare className="w-3.5 h-3.5" />}
                    >
                      Message
                    </Button>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}
    </div>
  );
};
