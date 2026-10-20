import React, { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { UserSummaryDTO } from '../../types/api';
import { Modal } from '../../components/ui/Modal';
import { Avatar } from '../../components/ui/Avatar';
import { Skeleton } from '../../components/ui/Skeleton';
import { DegreeBadge } from '../../components/ui/DegreeBadge';
import { Users, AlertTriangle, RefreshCw } from 'lucide-react';

export interface MutualConnectionsModalProps {
  isOpen: boolean;
  onClose: () => void;
  userId: string;
  userName: string;
  onSelectUser?: (userId: string) => void;
}

export const MutualConnectionsModal: React.FC<MutualConnectionsModalProps> = ({
  isOpen,
  onClose,
  userId,
  userName,
  onSelectUser,
}) => {
  const [mutuals, setMutuals] = useState<UserSummaryDTO[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMutuals = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.users.getMutuals(userId);
      setMutuals(data);
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve mutual connections.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchMutuals();
    }
  }, [isOpen, userId]);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Mutual Connections with ${userName}`}
      description="Colleagues and engineers you both are connected to directly."
      size="md"
    >
      <div className="space-y-3 min-h-[150px]">
        {/* Loading */}
        {loading && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center gap-3">
                <Skeleton variant="circular" width={40} height={40} />
                <div className="flex-1 space-y-1.5">
                  <Skeleton width="50%" height={14} />
                  <Skeleton width="80%" height={10} />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Error */}
        {!loading && error && (
          <div className="p-4 bg-warning-50 rounded-lg text-center">
            <AlertTriangle className="w-5 h-5 text-warning-600 mx-auto mb-1" />
            <p className="text-xs text-warning-800">{error}</p>
            <button
              onClick={fetchMutuals}
              className="mt-2 text-xs text-brand-600 font-semibold hover:underline inline-flex items-center gap-1"
            >
              <RefreshCw className="w-3 h-3" /> Retry
            </button>
          </div>
        )}

        {/* Empty */}
        {!loading && !error && mutuals.length === 0 && (
          <div className="py-8 text-center text-surface-500">
            <Users className="w-8 h-8 mx-auto mb-2 text-surface-300" />
            <p className="text-xs">No mutual 1st-degree connections found.</p>
          </div>
        )}

        {/* Populated */}
        {!loading && !error && mutuals.length > 0 && (
          <div className="divide-y divide-surface-100">
            {mutuals.map((user) => (
              <div
                key={user.id}
                onClick={() => {
                  onSelectUser?.(user.id);
                  onClose();
                }}
                className="py-3 flex items-center justify-between gap-3 hover:bg-surface-50 cursor-pointer rounded-lg px-2 transition-colors"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <Avatar src={user.avatar_url} alt={user.full_name} size="md" />
                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-bold text-surface-900 truncate">
                        {user.full_name}
                      </span>
                      <DegreeBadge degree="1st" />
                    </div>
                    <p className="text-[11px] text-surface-500 line-clamp-1">{user.headline}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Modal>
  );
};
