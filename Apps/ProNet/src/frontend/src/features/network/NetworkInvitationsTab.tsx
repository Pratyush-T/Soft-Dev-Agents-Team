import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { ConnectionDTO } from '../../types/api';
import { useWebSocketStore } from '../../stores/webSocketStore';
import { useToastStore } from '../../stores/toastStore';
import { Avatar } from '../../components/ui/Avatar';
import { Button } from '../../components/ui/Button';
import { Skeleton } from '../../components/ui/Skeleton';
import { Check, X, Clock, MailOpen, AlertTriangle, RefreshCw } from 'lucide-react';

export interface NetworkInvitationsTabProps {
  onSelectUser?: (userId: string) => void;
}

export const NetworkInvitationsTab: React.FC<NetworkInvitationsTabProps> = ({
  onSelectUser,
}) => {
  const [incoming, setIncoming] = useState<ConnectionDTO[]>([]);
  const [outgoing, setOutgoing] = useState<ConnectionDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionId, setActionId] = useState<string | null>(null);

  const { decrementBadge } = useWebSocketStore();
  const { addToast } = useToastStore();

  const fetchInvitations = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.connections.getPending();
      setIncoming(data.incoming);
      setOutgoing(data.outgoing);
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve connection invitations.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvitations();
  }, []);

  const handleAccept = async (connId: string, peerName: string) => {
    setActionId(connId);
    try {
      await api.connections.acceptRequest(connId);
      setIncoming((prev) => prev.filter((c) => c.id !== connId));
      decrementBadge('pending_connections');
      addToast({
        type: 'success',
        title: 'Connected',
        message: `Accepted connection from ${peerName}.`,
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Action Failed',
        message: err.message || 'Could not accept invitation.',
      });
    } finally {
      setActionId(null);
    }
  };

  const handleIgnore = async (connId: string) => {
    setActionId(connId);
    try {
      await api.connections.ignoreRequest(connId);
      setIncoming((prev) => prev.filter((c) => c.id !== connId));
      decrementBadge('pending_connections');
      addToast({
        type: 'info',
        title: 'Ignored',
        message: 'Connection invitation ignored.',
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Action Failed',
        message: err.message || 'Could not ignore invitation.',
      });
    } finally {
      setActionId(null);
    }
  };

  const handleWithdraw = async (connId: string) => {
    setActionId(connId);
    try {
      await api.connections.withdrawRequest(connId);
      setOutgoing((prev) => prev.filter((c) => c.id !== connId));
      addToast({
        type: 'info',
        title: 'Withdrawn',
        message: 'Invitation withdrawn.',
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Withdraw Failed',
        message: err.message || 'Could not withdraw invitation.',
      });
    } finally {
      setActionId(null);
    }
  };

  const totalPending = incoming.length + outgoing.length;

  return (
    <div className="space-y-6">
      {/* 1. Loading Skeleton */}
      {loading && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white p-4 rounded-xl border border-surface-200 flex items-center gap-4">
              <Skeleton variant="circular" width={48} height={48} />
              <div className="flex-1 space-y-1.5">
                <Skeleton width="40%" height={14} />
                <Skeleton width="70%" height={10} />
              </div>
              <div className="flex gap-2">
                <Skeleton width={80} height={32} />
                <Skeleton width={80} height={32} />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 2. Error State with Retry */}
      {!loading && error && (
        <div className="bg-white p-8 rounded-xl border border-danger-200 text-center space-y-3">
          <AlertTriangle className="w-8 h-8 text-danger-500 mx-auto" />
          <h4 className="text-sm font-bold text-surface-900">Unable to Retrieve Invitations</h4>
          <p className="text-xs text-surface-600">{error}</p>
          <Button
            variant="primary"
            size="sm"
            onClick={fetchInvitations}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Try Again
          </Button>
        </div>
      )}

      {/* 3. Empty State */}
      {!loading && !error && totalPending === 0 && (
        <div className="bg-white p-12 rounded-xl border border-surface-200 text-center space-y-3">
          <div className="w-14 h-14 bg-surface-100 rounded-full flex items-center justify-center mx-auto text-surface-400">
            <MailOpen className="w-7 h-7" />
          </div>
          <h4 className="text-base font-bold text-surface-900">No Pending Invitations</h4>
          <p className="text-xs text-surface-500 max-w-sm mx-auto">
            You are all caught up! New invitations sent to you or requests you send will appear here.
          </p>
        </div>
      )}

      {/* 4. Populated State */}
      {!loading && !error && totalPending > 0 && (
        <>
          {/* Section: Received Invitations */}
          {incoming.length > 0 && (
            <div className="bg-white rounded-xl border border-surface-200 shadow-elevation-1 overflow-hidden">
              <div className="p-4 bg-surface-50 border-b border-surface-200 flex items-center justify-between">
                <h3 className="text-sm font-bold text-surface-900">
                  Received Invitations ({incoming.length})
                </h3>
              </div>

              <div className="divide-y divide-surface-100">
                {incoming.map((item) => (
                  <div
                    key={item.id}
                    className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-surface-50/60 transition-colors"
                  >
                    <div
                      onClick={() => onSelectUser?.(item.peer.id)}
                      className="flex items-start gap-3 cursor-pointer group flex-1 min-w-0"
                    >
                      <Avatar src={item.peer.avatar_url} alt={item.peer.full_name} size="md" />
                      <div className="flex-1 min-w-0">
                        <span className="text-xs font-bold text-surface-900 group-hover:text-brand-600 transition-colors">
                          {item.peer.full_name}
                        </span>
                        <p className="text-[11px] text-surface-500 line-clamp-1">{item.peer.headline}</p>

                        {/* Optional note bubble */}
                        {item.note && (
                          <div className="mt-1.5 p-2 bg-brand-50/50 rounded-md border border-brand-100 text-xs text-surface-700 italic">
                            &quot;{item.note}&quot;
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => handleIgnore(item.id)}
                        disabled={actionId === item.id}
                        leftIcon={<X className="w-3.5 h-3.5" />}
                      >
                        Ignore
                      </Button>
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => handleAccept(item.id, item.peer.full_name)}
                        isLoading={actionId === item.id}
                        leftIcon={<Check className="w-3.5 h-3.5" />}
                      >
                        Accept
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Section: Sent Invitations */}
          {outgoing.length > 0 && (
            <div className="bg-white rounded-xl border border-surface-200 shadow-elevation-1 overflow-hidden">
              <div className="p-4 bg-surface-50 border-b border-surface-200 flex items-center justify-between">
                <h3 className="text-sm font-bold text-surface-900">
                  Sent Invitations ({outgoing.length})
                </h3>
              </div>

              <div className="divide-y divide-surface-100">
                {outgoing.map((item) => (
                  <div
                    key={item.id}
                    className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-surface-50/60 transition-colors"
                  >
                    <div
                      onClick={() => onSelectUser?.(item.peer.id)}
                      className="flex items-start gap-3 cursor-pointer group flex-1 min-w-0"
                    >
                      <Avatar src={item.peer.avatar_url} alt={item.peer.full_name} size="md" />
                      <div className="flex-1 min-w-0">
                        <span className="text-xs font-bold text-surface-900 group-hover:text-brand-600 transition-colors">
                          {item.peer.full_name}
                        </span>
                        <p className="text-[11px] text-surface-500 line-clamp-1">{item.peer.headline}</p>

                        <div className="flex items-center gap-1 text-[10px] text-surface-400 mt-1">
                          <Clock className="w-3 h-3" />
                          <span>
                            Sent on {new Date(item.created_at).toLocaleDateString([], { month: 'short', day: 'numeric' })}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="shrink-0 self-end sm:self-center">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleWithdraw(item.id)}
                        isLoading={actionId === item.id}
                      >
                        Withdraw Request
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
