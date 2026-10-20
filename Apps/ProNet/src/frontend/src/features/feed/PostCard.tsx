import React, { useState } from 'react';
import { api } from '../../services/api';
import { PostDTO, ReactionType } from '../../types/api';
import { useAuthStore } from '../../stores/authStore';
import { useToastStore } from '../../stores/toastStore';
import { Avatar } from '../../components/ui/Avatar';
import { DegreeBadge } from '../../components/ui/DegreeBadge';
import { ReactionPicker } from './ReactionPicker';
import { CommentThread } from './CommentThread';
import {
  ThumbsUp,
  MessageSquare,
  Share2,
  Trash2,
  Copy,
  Check,
  PartyPopper,
  Lightbulb,
} from 'lucide-react';

export interface PostCardProps {
  post: PostDTO;
  onDelete?: (postId: string) => void;
  onUserClick?: (userId: string) => void;
}

export const PostCard: React.FC<PostCardProps> = ({ post, onDelete, onUserClick }) => {
  const { currentUser } = useAuthStore();
  const { addToast } = useToastStore();

  const [viewerReaction, setViewerReaction] = useState<ReactionType | null>(post.viewer_reaction);
  const [likeCount, setLikeCount] = useState(post.like_count);
  const [celebrateCount, setCelebrateCount] = useState(post.celebrate_count);
  const [insightfulCount, setInsightfulCount] = useState(post.insightful_count);
  const [commentCount, setCommentCount] = useState(post.comment_count);

  const [showPicker, setShowPicker] = useState(false);
  const [showComments, setShowComments] = useState(false);
  const [codeCopied, setCodeCopied] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const isAuthor = currentUser?.id === post.author.id;
  const totalReactions = likeCount + celebrateCount + insightfulCount;

  const handleCopyCode = () => {
    if (post.code_snippet) {
      navigator.clipboard.writeText(post.code_snippet);
      setCodeCopied(true);
      setTimeout(() => setCodeCopied(false), 2000);
      addToast({
        type: 'info',
        title: 'Copied',
        message: 'Code snippet copied to clipboard.',
      });
    }
  };

  const handleReactionSelect = async (reactionType: ReactionType) => {
    setShowPicker(false);
    const prevReaction = viewerReaction;
    const prevLikes = likeCount;
    const prevCelebrates = celebrateCount;
    const prevInsightfuls = insightfulCount;

    // Optimistic state calculation
    if (prevReaction === reactionType) {
      // Toggle off
      setViewerReaction(null);
      if (reactionType === 'LIKE') setLikeCount((c) => Math.max(0, c - 1));
      if (reactionType === 'CELEBRATE') setCelebrateCount((c) => Math.max(0, c - 1));
      if (reactionType === 'INSIGHTFUL') setInsightfulCount((c) => Math.max(0, c - 1));

      try {
        await api.feed.removeReaction(post.id);
      } catch (err: any) {
        // Rollback
        setViewerReaction(prevReaction);
        setLikeCount(prevLikes);
        setCelebrateCount(prevCelebrates);
        setInsightfulCount(prevInsightfuls);
        addToast({ type: 'error', title: 'Error', message: 'Could not remove reaction' });
      }
    } else {
      // Toggle on or switch
      setViewerReaction(reactionType);

      // Decrement previous if existed
      if (prevReaction === 'LIKE') setLikeCount((c) => Math.max(0, c - 1));
      if (prevReaction === 'CELEBRATE') setCelebrateCount((c) => Math.max(0, c - 1));
      if (prevReaction === 'INSIGHTFUL') setInsightfulCount((c) => Math.max(0, c - 1));

      // Increment new
      if (reactionType === 'LIKE') setLikeCount((c) => c + 1);
      if (reactionType === 'CELEBRATE') setCelebrateCount((c) => c + 1);
      if (reactionType === 'INSIGHTFUL') setInsightfulCount((c) => c + 1);

      try {
        await api.feed.setReaction(post.id, { reaction_type: reactionType });
      } catch (err: any) {
        // Rollback
        setViewerReaction(prevReaction);
        setLikeCount(prevLikes);
        setCelebrateCount(prevCelebrates);
        setInsightfulCount(prevInsightfuls);
        addToast({ type: 'error', title: 'Error', message: 'Could not save reaction' });
      }
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this post?')) return;

    setIsDeleting(true);
    try {
      await api.feed.deletePost(post.id);
      addToast({
        type: 'info',
        title: 'Post Deleted',
        message: 'Your post was successfully deleted.',
      });
      onDelete?.(post.id);
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Delete Failed',
        message: err.message || 'Could not delete post.',
      });
      setIsDeleting(false);
    }
  };

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.origin + `?post=${post.id}`);
    addToast({
      type: 'success',
      title: 'Link Copied',
      message: 'Post link copied to clipboard.',
    });
  };

  return (
    <article
      className="bg-white rounded-xl border border-surface-200 shadow-elevation-1 p-4 sm:p-5 transition-shadow hover:shadow-elevation-2"
      role="article"
      aria-label={`Post by ${post.author.full_name}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div
          onClick={() => onUserClick?.(post.author.id)}
          className="flex items-start gap-3 cursor-pointer group flex-1 min-w-0"
        >
          <Avatar
            src={post.author.avatar_url}
            alt={post.author.full_name}
            size="md"
          />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-sm font-bold text-surface-900 group-hover:text-brand-600 transition-colors truncate">
                {post.author.full_name}
              </span>
              <DegreeBadge degree={post.is_author_connection ? '1st' : '2nd'} />
            </div>
            <p className="text-xs text-surface-500 line-clamp-1">{post.author.headline}</p>
            <span className="text-[11px] text-surface-400">
              {new Date(post.created_at).toLocaleDateString([], {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </span>
          </div>
        </div>

        {/* Delete button for author */}
        {isAuthor && (
          <button
            onClick={handleDelete}
            disabled={isDeleting}
            className="p-1.5 text-surface-400 hover:text-danger-600 hover:bg-danger-50 rounded-lg transition-colors"
            title="Delete post"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Post Text Body */}
      <div className="text-sm text-surface-800 leading-relaxed whitespace-pre-wrap mb-3">
        {post.content}
      </div>

      {/* Code Snippet Box */}
      {post.code_snippet && (
        <div className="mb-3 rounded-lg overflow-hidden border border-surface-700 bg-surface-900 text-surface-100">
          <div className="flex items-center justify-between px-3 py-1.5 bg-surface-950/80 border-b border-surface-800 text-[11px]">
            <span className="font-mono text-surface-400 uppercase">
              {post.code_language || 'code'}
            </span>
            <button
              onClick={handleCopyCode}
              className="flex items-center gap-1 text-surface-400 hover:text-white transition-colors"
            >
              {codeCopied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-success-500" />
                  <span className="text-success-500">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>
          <pre className="p-3 text-xs font-mono overflow-x-auto text-surface-200">
            <code>{post.code_snippet}</code>
          </pre>
        </div>
      )}

      {/* Attached Image */}
      {post.image_url && (
        <div className="mb-3 rounded-lg overflow-hidden border border-surface-200 bg-surface-50 max-h-96">
          <img
            src={post.image_url}
            alt="Attached media"
            className="w-full h-auto object-cover max-h-96"
            loading="lazy"
          />
        </div>
      )}

      {/* Engagement Counter Bar */}
      <div className="flex items-center justify-between text-xs text-surface-500 py-2 border-b border-surface-100">
        <div className="flex items-center gap-1.5">
          {totalReactions > 0 ? (
            <>
              <div className="flex -space-x-1">
                {likeCount > 0 && (
                  <span className="w-4 h-4 rounded-full bg-brand-600 text-white flex items-center justify-center text-[9px] shadow-sm">
                    <ThumbsUp className="w-2.5 h-2.5" />
                  </span>
                )}
                {celebrateCount > 0 && (
                  <span className="w-4 h-4 rounded-full bg-success-600 text-white flex items-center justify-center text-[9px] shadow-sm">
                    <PartyPopper className="w-2.5 h-2.5" />
                  </span>
                )}
                {insightfulCount > 0 && (
                  <span className="w-4 h-4 rounded-full bg-warning-600 text-white flex items-center justify-center text-[9px] shadow-sm">
                    <Lightbulb className="w-2.5 h-2.5" />
                  </span>
                )}
              </div>
              <span>{totalReactions} reactions</span>
            </>
          ) : (
            <span>No reactions yet</span>
          )}
        </div>

        <button
          onClick={() => setShowComments(!showComments)}
          className="hover:text-brand-600 transition-colors"
        >
          {commentCount} {commentCount === 1 ? 'comment' : 'comments'}
        </button>
      </div>

      {/* Interactive Action Bar */}
      <div className="flex items-center justify-between pt-1 relative">
        {/* Floating Reaction Picker Dock */}
        {showPicker && (
          <div
            className="absolute bottom-11 left-0 z-20"
            onMouseLeave={() => setShowPicker(false)}
          >
            <ReactionPicker
              onSelect={handleReactionSelect}
              activeReaction={viewerReaction}
            />
          </div>
        )}

        {/* Reaction Trigger Button */}
        <div
          className="relative"
          onMouseEnter={() => setShowPicker(true)}
        >
          <button
            onClick={() => handleReactionSelect(viewerReaction || 'LIKE')}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${
              viewerReaction === 'LIKE'
                ? 'text-brand-600 bg-brand-50'
                : viewerReaction === 'CELEBRATE'
                ? 'text-success-600 bg-success-50'
                : viewerReaction === 'INSIGHTFUL'
                ? 'text-warning-600 bg-warning-50'
                : 'text-surface-600 hover:bg-surface-100 hover:text-surface-900'
            }`}
          >
            {viewerReaction === 'LIKE' ? (
              <ThumbsUp className="w-4 h-4 fill-brand-600/20" />
            ) : viewerReaction === 'CELEBRATE' ? (
              <PartyPopper className="w-4 h-4" />
            ) : viewerReaction === 'INSIGHTFUL' ? (
              <Lightbulb className="w-4 h-4 fill-warning-600/20" />
            ) : (
              <ThumbsUp className="w-4 h-4" />
            )}
            <span>
              {viewerReaction === 'LIKE'
                ? 'Liked'
                : viewerReaction === 'CELEBRATE'
                ? 'Celebrated'
                : viewerReaction === 'INSIGHTFUL'
                ? 'Insightful'
                : 'Like'}
            </span>
          </button>
        </div>

        {/* Comment Trigger Button */}
        <button
          onClick={() => setShowComments(!showComments)}
          className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${
            showComments
              ? 'text-brand-600 bg-brand-50'
              : 'text-surface-600 hover:bg-surface-100 hover:text-surface-900'
          }`}
        >
          <MessageSquare className="w-4 h-4" />
          <span>Comment</span>
        </button>

        {/* Share Button */}
        <button
          onClick={handleShare}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold text-surface-600 hover:bg-surface-100 hover:text-surface-900 transition-colors"
        >
          <Share2 className="w-4 h-4" />
          <span>Share</span>
        </button>
      </div>

      {/* Expandable Threaded Comments Section */}
      {showComments && (
        <div className="mt-3">
          <CommentThread
            postId={post.id}
            isPostAuthor={isAuthor}
            onCommentCountChange={(delta) => setCommentCount((c) => Math.max(0, c + delta))}
          />
        </div>
      )}
    </article>
  );
};
