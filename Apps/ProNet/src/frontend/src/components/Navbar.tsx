import React, { useState } from 'react';
import { PersonaQuickSwitcher } from './PersonaQuickSwitcher';
import { NotificationsDrawer } from '../features/notifications/NotificationsDrawer';
import { useWebSocketStore } from '../stores/webSocketStore';
import { useAuthStore } from '../stores/authStore';
import { useChatStore } from '../stores/chatStore';
import {
  Home,
  Users,
  Briefcase,
  MessageSquare,
  Bell,
  Search,
  User as UserIcon,
} from 'lucide-react';

export interface NavbarProps {
  currentTab: string;
  onSelectTab: (tab: string, param?: string) => void;
  onSearch?: (query: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, onSelectTab, onSearch }) => {
  const { badges } = useWebSocketStore();
  const { currentUser } = useAuthStore();
  const { setDockOpen } = useChatStore();
  const [isNotifOpen, setIsNotifOpen] = useState(false);
  const [searchValue, setSearchValue] = useState('');

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (onSearch) {
      onSearch(searchValue);
    }
  };

  return (
    <header className="sticky top-0 z-40 bg-white border-b border-surface-200 shadow-sm" role="banner">
      <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between gap-4">
        {/* Left: Branding & Global Search */}
        <div className="flex items-center gap-3 flex-1 max-w-md">
          {/* Logo */}
          <button
            onClick={() => onSelectTab('feed')}
            className="flex items-center gap-1.5 shrink-0 focus-visible:outline-none"
            aria-label="ProNet Home"
          >
            <div className="w-8 h-8 rounded-md bg-brand-600 flex items-center justify-center text-white font-black text-lg tracking-tighter shadow-sm">
              in
            </div>
            <span className="font-bold text-lg text-surface-900 tracking-tight hidden sm:inline">
              Pro<span className="text-brand-600">Net</span>
            </span>
          </button>

          {/* Global Search */}
          <form onSubmit={handleSearchSubmit} className="relative flex-1 hidden md:block">
            <Search className="w-4 h-4 text-surface-400 absolute left-3 top-2.5 pointer-events-none" />
            <input
              type="text"
              placeholder="Search posts, jobs, engineers..."
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              className="w-full pl-9 pr-4 py-1.5 text-xs rounded-md bg-surface-100 border border-transparent focus:border-brand-600 focus:bg-white focus:outline-none transition-all placeholder:text-surface-400"
            />
          </form>
        </div>

        {/* Center/Right: Navigation Tabs & Badges */}
        <nav className="flex items-center gap-1 sm:gap-2" role="navigation" aria-label="Main Navigation">
          {/* Feed */}
          <button
            onClick={() => onSelectTab('feed')}
            className={`flex flex-col items-center justify-center min-w-[50px] sm:min-w-[64px] h-14 px-1 border-b-2 transition-colors ${
              currentTab === 'feed'
                ? 'border-brand-600 text-brand-600 font-semibold'
                : 'border-transparent text-surface-500 hover:text-surface-900'
            }`}
          >
            <Home className="w-5 h-5" />
            <span className="text-[10px] mt-0.5 hidden sm:inline">Feed</span>
          </button>

          {/* Network */}
          <button
            onClick={() => onSelectTab('network')}
            className={`relative flex flex-col items-center justify-center min-w-[50px] sm:min-w-[64px] h-14 px-1 border-b-2 transition-colors ${
              currentTab === 'network'
                ? 'border-brand-600 text-brand-600 font-semibold'
                : 'border-transparent text-surface-500 hover:text-surface-900'
            }`}
          >
            <Users className="w-5 h-5" />
            <span className="text-[10px] mt-0.5 hidden sm:inline">Network</span>
            {badges.pending_connections > 0 && (
              <span className="absolute top-1.5 right-2 sm:right-4 bg-danger-600 text-white text-[10px] font-bold px-1.5 py-0.2 rounded-full min-w-[16px] text-center">
                {badges.pending_connections > 9 ? '9+' : badges.pending_connections}
              </span>
            )}
          </button>

          {/* Jobs */}
          <button
            onClick={() => onSelectTab('jobs')}
            className={`flex flex-col items-center justify-center min-w-[50px] sm:min-w-[64px] h-14 px-1 border-b-2 transition-colors ${
              currentTab === 'jobs'
                ? 'border-brand-600 text-brand-600 font-semibold'
                : 'border-transparent text-surface-500 hover:text-surface-900'
            }`}
          >
            <Briefcase className="w-5 h-5" />
            <span className="text-[10px] mt-0.5 hidden sm:inline">Jobs</span>
          </button>

          {/* Messaging (triggers ChatDock) */}
          <button
            onClick={() => setDockOpen(true)}
            className="relative flex flex-col items-center justify-center min-w-[50px] sm:min-w-[64px] h-14 px-1 border-b-2 border-transparent text-surface-500 hover:text-surface-900 transition-colors"
          >
            <MessageSquare className="w-5 h-5" />
            <span className="text-[10px] mt-0.5 hidden sm:inline">Messaging</span>
            {badges.unread_messages > 0 && (
              <span className="absolute top-1.5 right-2 sm:right-4 bg-danger-600 text-white text-[10px] font-bold px-1.5 py-0.2 rounded-full min-w-[16px] text-center">
                {badges.unread_messages > 9 ? '9+' : badges.unread_messages}
              </span>
            )}
          </button>

          {/* Notifications */}
          <div className="relative">
            <button
              onClick={() => setIsNotifOpen(!isNotifOpen)}
              className={`relative flex flex-col items-center justify-center min-w-[50px] sm:min-w-[64px] h-14 px-1 border-b-2 transition-colors ${
                isNotifOpen
                  ? 'border-brand-600 text-brand-600 font-semibold'
                  : 'border-transparent text-surface-500 hover:text-surface-900'
              }`}
              aria-label="Toggle notifications menu"
            >
              <Bell className="w-5 h-5" />
              <span className="text-[10px] mt-0.5 hidden sm:inline">Alerts</span>
              {badges.unread_notifications > 0 && (
                <span className="absolute top-1.5 right-2 sm:right-4 bg-danger-600 text-white text-[10px] font-bold px-1.5 py-0.2 rounded-full min-w-[16px] text-center">
                  {badges.unread_notifications > 9 ? '9+' : badges.unread_notifications}
                </span>
              )}
            </button>
            <NotificationsDrawer
              isOpen={isNotifOpen}
              onClose={() => setIsNotifOpen(false)}
              onNavigate={(tab) => onSelectTab(tab)}
            />
          </div>

          {/* My Profile shortcut */}
          <button
            onClick={() => {
              if (currentUser) {
                onSelectTab('profile', currentUser.id);
              }
            }}
            className={`flex flex-col items-center justify-center min-w-[45px] sm:min-w-[55px] h-14 px-1 border-b-2 transition-colors ${
              currentTab === 'profile'
                ? 'border-brand-600 text-brand-600 font-semibold'
                : 'border-transparent text-surface-500 hover:text-surface-900'
            }`}
            title="View my own profile"
          >
            <UserIcon className="w-5 h-5" />
            <span className="text-[10px] mt-0.5 hidden sm:inline">Me</span>
          </button>

          {/* Divider */}
          <div className="h-6 w-px bg-surface-200 mx-1 hidden sm:block" />

          {/* The Prominent 1-Click Persona Quick-Switcher */}
          <PersonaQuickSwitcher />
        </nav>
      </div>
    </header>
  );
};
