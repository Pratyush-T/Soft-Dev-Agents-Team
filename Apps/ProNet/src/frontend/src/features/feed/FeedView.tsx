import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../../services/api';
import { FeedMode, PostDTO } from '../../types/api';
import { useAuthStore } from '../../stores/authStore';
import { PostCard } from './PostCard';
import { PostComposerModal } from './PostComposerModal';
import { Avatar } from '../../components/ui/Avatar';
import { Button } from '../../components/ui/Button';
import { Skeleton } from '../../components/ui/Skeleton';
import {
  Code2,
  Image as ImageIcon,
  Sparkles,
  Clock,
  TrendingUp,
  AlertTriangle,
  RefreshCw,
  Newspaper,
  Plus,
} from 'lucide-react';

export interface FeedViewProps {
  onNavigateToProfile?: (userId: string) => void;
  onNavigateToNetwork?: () => void;
}

export const FeedView: React.FC<FeedViewProps> = ({
  onNavigateToProfile,
  onNavigateToNetwork,
}) => {
  const { currentUser } = useAuthStore();
  const [posts, setPosts] = useState<PostDTO[]>([]);
  const [feedMode, setFeedMode] = useState<FeedMode>('recent');
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isComposerOpen, setIsComposerOpen] = useState(false);

  const fetchFeed = useCallback(
    async (mode: FeedMode, cursor?: string, append: boolean = false) => {
      if (append) {
        setLoadingMore(true);
      } else {
        setLoading(true);
        setError(null);
      }

      try {
        const data = await api.feed.getFeed(mode, cursor, 20);
        if (append) {
          setPosts((prev) => [...prev, ...data.items]);
        } else {
          setPosts(data.items);
        }
        setNextCursor(data.next_cursor);
        setHasMore(data.has_more);
      } catch (err: any) {
        setError(err.message || 'Unable to retrieve activity feed.');
      } finally {
        setLoading(false);
        setLoadingMore(false);
      }
    },
    []
  );

  useEffect(() => {
    fetchFeed(feedMode);
  }, [feedMode, fetchFeed]);

  const handlePostCreated = (newPost: PostDTO) => {
    setPosts((prev) => [newPost, ...prev]);
  };

  const handlePostDeleted = (deletedPostId: string) => {
    setPosts((prev) => prev.filter((p) => p.id !== deletedPostId));
  };

  const handleLoadMore = () => {
    if (nextCursor && !loadingMore) {
      fetchFeed(feedMode, nextCursor, true);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <div className="flex flex-col lg:flex-row gap-6 items-start">
        {/* Left Column: Mini Profile & Network Shortcuts (w-64) */}
        <aside className="w-full lg:w-64 shrink-0 space-y-4" aria-label="Personal Overview">
          {/* Profile Card */}
          <div className="bg-white rounded-xl border border-surface-200 shadow-elevation-1 overflow-hidden">
            {/* Banner */}
            <div className="h-16 bg-gradient-to-r from-brand-700 via-brand-600 to-brand-500" />
            <div className="px-4 pb-4 pt-0 text-center relative">
              <div className="flex justify-center -mt-8 mb-2">
                <Avatar
                  src={currentUser?.avatar_url || null}
                  alt={currentUser?.full_name || 'Me'}
                  size="lg"
                  className="ring-4 ring-white"
                />
              </div>
              <button
                onClick={() => currentUser && onNavigateToProfile?.(currentUser.id)}
                className="text-sm font-bold text-surface-900 hover:text-brand-600 transition-colors block mx-auto"
              >
                {currentUser?.full_name || 'Professional User'}
              </button>
              <p className="text-xs text-surface-500 line-clamp-2 mt-0.5">
                {currentUser?.headline || 'Member of ProNet Engineering Community'}
              </p>

              <div className="mt-4 pt-3 border-t border-surface-100 flex justify-between text-xs text-surface-600">
                <span>Network Connections</span>
                <button
                  onClick={onNavigateToNetwork}
                  className="font-bold text-brand-600 hover:underline"
                >
                  Manage
                </button>
              </div>
            </div>
          </div>

          {/* Quick Info Box */}
          <div className="bg-white rounded-xl border border-surface-200 shadow-elevation-1 p-4 hidden lg:block">
            <h4 className="text-xs font-bold text-surface-700 uppercase tracking-wider mb-2">
              Platform Features
            </h4>
            <ul className="text-xs text-surface-600 space-y-2">
              <li className="flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-brand-600 shrink-0" />
                <span>Deterministic Graph Seeding</span>
              </li>
              <li className="flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-brand-600 shrink-0" />
                <span>Dual-mode Algorithmic Feed</span>
              </li>
              <li className="flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-brand-600 shrink-0" />
                <span>Full-Duplex Direct Messaging</span>
              </li>
            </ul>
          </div>
        </aside>

        {/* Center Column: Feed Stream (max-w-2xl flex-1) */}
        <main className="flex-1 w-full max-w-2xl space-y-4" role="main">
          {/* Post Composer Trigger Card */}
          <div className="bg-white rounded-xl border border-surface-200 shadow-elevation-1 p-4">
            <div className="flex items-center gap-3">
              <Avatar
                src={currentUser?.avatar_url || null}
                alt={currentUser?.full_name || 'Me'}
                size="md"
              />
              <button
                onClick={() => setIsComposerOpen(true)}
                className="flex-1 text-left px-4 py-2.5 text-xs text-surface-500 bg-surface-100 hover:bg-surface-200/80 rounded-full border border-surface-200 transition-colors font-medium"
              >
                Start a post, share architecture insights, or code...
              </button>
            </div>

            <div className="flex items-center justify-around mt-3 pt-3 border-t border-surface-100">
              <button
                onClick={() => setIsComposerOpen(true)}
                className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold text-surface-600 hover:bg-surface-100 rounded-lg transition-colors"
              >
                <ImageIcon className="w-4 h-4 text-brand-500" />
                <span>Media</span>
              </button>

              <button
                onClick={() => setIsComposerOpen(true)}
                className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold text-surface-600 hover:bg-surface-100 rounded-lg transition-colors"
              >
                <Code2 className="w-4 h-4 text-emerald-600" />
                <span>Code Block</span>
              </button>

              <button
                onClick={() => setIsComposerOpen(true)}
                className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold text-brand-600 hover:bg-brand-50 rounded-lg transition-colors"
              >
                <Plus className="w-4 h-4" />
                <span>New Post</span>
              </button>
            </div>
          </div>

          {/* Dual-Mode Sort Toggle Bar */}
          <div className="flex items-center justify-between px-2 text-xs">
            <div className="h-px bg-surface-200 flex-1 mr-3" />
            <div className="flex items-center gap-1 bg-surface-200/60 p-1 rounded-lg">
              <button
                onClick={() => setFeedMode('recent')}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-md font-semibold transition-all ${
                  feedMode === 'recent'
                    ? 'bg-white text-brand-600 shadow-sm'
                    : 'text-surface-600 hover:text-surface-900'
                }`}
              >
                <Clock className="w-3.5 h-3.5" />
                <span>Recent</span>
              </button>

              <button
                onClick={() => setFeedMode('top')}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-md font-semibold transition-all ${
                  feedMode === 'top'
                    ? 'bg-white text-brand-600 shadow-sm'
                    : 'text-surface-600 hover:text-surface-900'
                }`}
              >
                <TrendingUp className="w-3.5 h-3.5" />
                <span>Top Engagement</span>
              </button>
            </div>
          </div>

          {/* 1. Loading Skeleton State */}
          {loading && (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="bg-white rounded-xl border border-surface-200 p-5 space-y-4">
                  <div className="flex items-center gap-3">
                    <Skeleton variant="circular" width={40} height={40} />
                    <div className="space-y-1.5 flex-1">
                      <Skeleton width="40%" height={14} />
                      <Skeleton width="65%" height={10} />
                    </div>
                  </div>
                  <Skeleton width="100%" height={14} />
                  <Skeleton width="85%" height={14} />
                  <Skeleton width="100%" height={120} />
                </div>
              ))}
            </div>
          )}

          {/* 2. Error State with Retry */}
          {!loading && error && (
            <div className="bg-white rounded-xl border border-danger-200 p-8 text-center space-y-3">
              <div className="w-12 h-12 bg-danger-50 rounded-full flex items-center justify-center mx-auto text-danger-600">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <h3 className="text-sm font-bold text-surface-900">Unable to Load Activity Feed</h3>
              <p className="text-xs text-surface-600 max-w-sm mx-auto">{error}</p>
              <Button
                variant="primary"
                size="sm"
                onClick={() => fetchFeed(feedMode)}
                leftIcon={<RefreshCw className="w-4 h-4" />}
              >
                Retry Feed
              </Button>
            </div>
          )}

          {/* 3. Empty State with CTA */}
          {!loading && !error && posts.length === 0 && (
            <div className="bg-white rounded-xl border border-surface-200 p-10 text-center space-y-3">
              <div className="w-14 h-14 bg-brand-50 rounded-full flex items-center justify-center mx-auto text-brand-600">
                <Newspaper className="w-7 h-7" />
              </div>
              <h3 className="text-base font-bold text-surface-900">Your Feed is Quiet</h3>
              <p className="text-xs text-surface-600 max-w-sm mx-auto">
                Be the first to share an architectural insight, technical learning, or industry update with the ProNet network.
              </p>
              <Button
                variant="primary"
                size="md"
                onClick={() => setIsComposerOpen(true)}
                leftIcon={<Plus className="w-4 h-4" />}
              >
                Start a Post
              </Button>
            </div>
          )}

          {/* 4. Populated State */}
          {!loading && !error && posts.length > 0 && (
            <div className="space-y-4" role="feed">
              {posts.map((post) => (
                <PostCard
                  key={post.id}
                  post={post}
                  onDelete={handlePostDeleted}
                  onUserClick={onNavigateToProfile}
                />
              ))}

              {/* Load More Button */}
              {hasMore && (
                <div className="text-center pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleLoadMore}
                    isLoading={loadingMore}
                  >
                    Load More Posts
                  </Button>
                </div>
              )}
            </div>
          )}
        </main>

        {/* Right Column: Trending News & Recommendations (w-80) */}
        <aside className="w-full lg:w-80 shrink-0 space-y-4 hidden lg:block" aria-label="Community Insights">
          <div className="bg-white rounded-xl border border-surface-200 shadow-elevation-1 p-4">
            <h4 className="text-xs font-bold text-surface-900 flex items-center gap-1.5 mb-3">
              <TrendingUp className="w-4 h-4 text-brand-600" />
              Trending in Tech & Systems
            </h4>
            <div className="space-y-3 text-xs">
              <div>
                <a href="#feed" className="font-semibold text-surface-800 hover:text-brand-600 block leading-tight">
                  SQLite Write-Ahead Logging at Scale
                </a>
                <span className="text-[10px] text-surface-400">4,120 readers • Architecture</span>
              </div>
              <div>
                <a href="#feed" className="font-semibold text-surface-800 hover:text-brand-600 block leading-tight">
                  FastAPI Async Concurrency Benchmarks
                </a>
                <span className="text-[10px] text-surface-400">2,840 readers • Python Backend</span>
              </div>
              <div>
                <a href="#feed" className="font-semibold text-surface-800 hover:text-brand-600 block leading-tight">
                  React 18 Concurrent Rendering Patterns
                </a>
                <span className="text-[10px] text-surface-400">1,990 readers • UI Engineering</span>
              </div>
              <div>
                <a href="#feed" className="font-semibold text-surface-800 hover:text-brand-600 block leading-tight">
                  eBPF Observability in Distributed Services
                </a>
                <span className="text-[10px] text-surface-400">1,430 readers • SRE Systems</span>
              </div>
            </div>
          </div>

          <div className="text-[11px] text-surface-400 px-2 space-y-1">
            <div className="flex gap-2 flex-wrap">
              <span>About ProNet</span>
              <span>Accessibility</span>
              <span>Privacy & Terms</span>
            </div>
            <p>ProNet Corporation © 2026. Enterprise Local-First Edition.</p>
          </div>
        </aside>
      </div>

      {/* Composer Modal */}
      <PostComposerModal
        isOpen={isComposerOpen}
        onClose={() => setIsComposerOpen(false)}
        onSuccess={handlePostCreated}
      />
    </div>
  );
};
