import React, { useEffect, useState } from 'react';
import { Navbar } from './components/Navbar';
import { ToastContainer } from './components/ToastContainer';
import { ChatDock } from './components/ChatDock';
import { FeedView } from './features/feed/FeedView';
import { ProfileView } from './features/profile/ProfileView';
import { NetworkView } from './features/network/NetworkView';
import { JobsView } from './features/jobs/JobsView';
import { useAuthStore } from './stores/authStore';

export const App: React.FC = () => {
  const { initializeSession, currentUser, isLoading } = useAuthStore();
  const [currentTab, setCurrentTab] = useState<'feed' | 'network' | 'jobs' | 'profile'>('feed');
  const [selectedProfileUserId, setSelectedProfileUserId] = useState<string | null>(null);

  useEffect(() => {
    initializeSession();
  }, [initializeSession]);

  const handleSelectTab = (tab: string, param?: string) => {
    if (tab === 'profile') {
      if (param) {
        setSelectedProfileUserId(param);
      } else if (currentUser) {
        setSelectedProfileUserId(currentUser.id);
      }
    }
    setCurrentTab(tab as 'feed' | 'network' | 'jobs' | 'profile');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleNavigateToProfile = (userId: string) => {
    setSelectedProfileUserId(userId);
    setCurrentTab('profile');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleGlobalSearch = (_query: string) => {
    setCurrentTab('jobs');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  if (isLoading && !currentUser) {
    return (
      <div className="min-h-screen bg-surface-50 flex flex-col items-center justify-center p-4">
        <div className="text-center space-y-4">
          <div className="w-12 h-12 rounded-xl bg-brand-600 text-white font-black text-2xl flex items-center justify-center mx-auto shadow-md animate-pulse">
            in
          </div>
          <div className="space-y-1">
            <h1 className="text-lg font-bold text-surface-900">ProNet Enterprise Network</h1>
            <p className="text-xs text-surface-500">Initializing session &amp; deterministic graph...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface-50 text-surface-900 flex flex-col selection:bg-brand-500 selection:text-white">
      {/* Top Fixed Header with Persona Switcher */}
      <Navbar
        currentTab={currentTab}
        onSelectTab={handleSelectTab}
        onSearch={handleGlobalSearch}
      />

      {/* Main Content Area */}
      <main className="flex-1 pb-16">
        {currentTab === 'feed' && (
          <FeedView
            onNavigateToProfile={handleNavigateToProfile}
            onNavigateToNetwork={() => setCurrentTab('network')}
          />
        )}

        {currentTab === 'network' && (
          <NetworkView
            onSelectUser={handleNavigateToProfile}
            onDiscoverPeers={() => setCurrentTab('feed')}
          />
        )}

        {currentTab === 'jobs' && (
          <JobsView
            onSelectUser={handleNavigateToProfile}
          />
        )}

        {currentTab === 'profile' && (
          <ProfileView
            userId={selectedProfileUserId || currentUser?.id || 'usr_elena_rostova'}
            onSelectUser={handleNavigateToProfile}
            onBackToFeed={() => setCurrentTab('feed')}
          />
        )}
      </main>

      {/* Bottom Floating Real-Time Chat Dock */}
      <ChatDock />

      {/* Global Toast Notifications Stack */}
      <ToastContainer />
    </div>
  );
};

export default App;
