import React, { useState } from 'react';
import { NetworkConnectionsTab } from './NetworkConnectionsTab';
import { NetworkInvitationsTab } from './NetworkInvitationsTab';
import { useWebSocketStore } from '../../stores/webSocketStore';
import { Users, MailOpen } from 'lucide-react';

export interface NetworkViewProps {
  onSelectUser?: (userId: string) => void;
  onDiscoverPeers?: () => void;
}

export const NetworkView: React.FC<NetworkViewProps> = ({
  onSelectUser,
  onDiscoverPeers,
}) => {
  const [activeTab, setActiveTab] = useState<'connections' | 'invitations'>('connections');
  const { badges } = useWebSocketStore();

  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      {/* Top Header & Navigation Tabs */}
      <div className="bg-white rounded-xl border border-surface-200 shadow-elevation-1 p-2 sm:p-3 mb-6">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab('connections')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === 'connections'
                ? 'bg-brand-600 text-white shadow-sm'
                : 'text-surface-600 hover:text-surface-900 hover:bg-surface-100'
            }`}
          >
            <Users className="w-4 h-4" />
            <span>My Connections</span>
          </button>

          <button
            onClick={() => setActiveTab('invitations')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs font-bold transition-all relative ${
              activeTab === 'invitations'
                ? 'bg-brand-600 text-white shadow-sm'
                : 'text-surface-600 hover:text-surface-900 hover:bg-surface-100'
            }`}
          >
            <MailOpen className="w-4 h-4" />
            <span>Invitations</span>
            {badges.pending_connections > 0 && (
              <span
                className={`text-[10px] font-bold px-1.5 py-0.2 rounded-full ${
                  activeTab === 'invitations'
                    ? 'bg-white text-brand-700'
                    : 'bg-danger-600 text-white'
                }`}
              >
                {badges.pending_connections}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Tab Panels */}
      {activeTab === 'connections' ? (
        <NetworkConnectionsTab
          onSelectUser={onSelectUser}
          onDiscoverPeers={onDiscoverPeers}
        />
      ) : (
        <NetworkInvitationsTab onSelectUser={onSelectUser} />
      )}
    </div>
  );
};
