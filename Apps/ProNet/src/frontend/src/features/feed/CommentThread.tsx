import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { CommentDTO } from '../../types/api';
import { useAuthStore } from '../../stores/authStore';
import { useToastStore } from '../../stores/toastStore';
import { Avatar } from '../../components/ui/Avatar';
import { Button } from '../../components/ui/Button';
import { Skeleton } from '../../components/ui/Skeleton';
import { CornerDownRight, Trash2, Send, AlertTriangle, RefreshCw } from 'lucide-react';

export interface CommentThreadProps {
  postId: string;
  isPostAuthor: boolean;
  onCommentCountChange?: (delta: number) => void;
}

export const CommentThread: React.FC<CommentThreadProps> = ({
  postId,
  isPostAuthor,
  onCommentCountChange,
}) => {
  const { currentUser } = useAuthStore();
  const { addToast } = useToastStore();

  const [comments, setComments] = useState<CommentDTO[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [rootText, setRootText] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Replying state: parent comment id being replied to
  const [replyingToId, setReplyingToId] = useState<string | null>(null);
  const [replyText, setReplyText] = useState('');
  const [submittingReply, setSubmittingReply] = useState(false);

  const fetchComments = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.feed.getComments(postId);
      setComments(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load comments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComments();
  }, [postId]);

  const handleAddRootComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rootText.trim()) return;

    setSubmitting(true);
    try {
      const newComment = await api.feed.addComment(postId, { content: rootText.trim() });
      setComments((prev) => [...prev, newComment]);
      setRootText('');
      onCommentCountChange?.(1);
      addToast({
        type: 'success',
        title: 'Comment Posted',
        message: 'Your comment was added successfully.',
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Comment Failed',
        message: err.message || 'Could not post comment.',
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddReply = async (parentId: string) => {
    if (!replyText.trim()) return;

    setSubmittingReply(true);
    try {
      const newReply = await api.feed.addComment(postId, {
        content: replyText.trim(),
        parent_id: parentId,
      });

      // Update parent's replies list in state
      setComments((prev) =>
        prev.map((c) => {
          if (c.id === parentId) {
            return {
              ...c,
              replies: [...(c.replies || []), newReply],
            };
          }
          return c;
        })
      );

      setReplyText('');
      setReplyingToId(null);
      onCommentCountChange?.(1);
      addToast({
        type: 'success',
        title: 'Reply Posted',
        message: 'Your reply has been published.',
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Reply Failed',
        message: err.message || 'Could not post reply.',
      });
    } finally {
      setSubmittingReply(false);
    }
  };

  const handleDeleteComment = async (commentId: string, isReply: boolean, parentId?: string) => {
    try {
      await api.feed.deleteComment(commentId);
      if (isReply && parentId) {
        setComments((prev) =>
          prev.map((c) =>
            c.id === parentId
              ? { ...c, replies: (c.replies || []).filter((r) => r.id !== commentId) }
              : c
          )
        );
      } else {
        setComments((prev) => prev.filter((c) => c.id !== commentId));
      }
      onCommentCountChange?.(-1);
      addToast({
        type: 'info',
        title: 'Comment Removed',
        message: 'The comment was deleted.',
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Delete Failed',
        message: err.message || 'Could not delete comment.',
      });
    }
  };

  return (
    <div className="pt-3 border-t border-surface-200 space-y-4">
      {/* Root Composer */}
      <form onSubmit={handleAddRootComment} className="flex gap-2.5 items-start">
        <Avatar src={currentUser?.avatar_url || null} alt={currentUser?.full_name || 'Me'} size="sm" />
        <div className="flex-1 relative">
          <input
            type="text"
            placeholder="Add a thought or insight..."
            value={rootText}
            onChange={(e) => setRootText(e.target.value)}
            className="w-full text-xs rounded-full border border-surface-200 bg-surface-50 py-2 pl-4 pr-12 focus:outline-none focus:border-brand-600 focus:bg-white focus:ring-1 focus:ring-brand-600 transition-colors"
          />
          <button
            type="submit"
            disabled={!rootText.trim() || submitting}
            className="absolute right-1.5 top-1 p-1 rounded-full text-brand-600 hover:bg-brand-50 disabled:opacity-40 disabled:hover:bg-transparent transition-colors"
            title="Post comment"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </form>

      {/* Loading Skeleton */}
      {loading && (
        <div className="space-y-3 py-2">
          {[1, 2].map((i) => (
            <div key={i} className="flex gap-2.5 items-start">
              <Skeleton variant="circular" width={28} height={28} />
              <div className="flex-1 space-y-1">
                <Skeleton width="40%" height={12} />
                <Skeleton width="85%" height={10} />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error with Retry */}
      {!loading && error && (
        <div className="p-4 bg-warning-50 rounded-lg text-center">
          <AlertTriangle className="w-5 h-5 text-warning-600 mx-auto mb-1" />
          <p className="text-xs text-warning-800 font-medium">{error}</p>
          <button
            onClick={fetchComments}
            className="mt-2 inline-flex items-center gap-1 text-xs text-brand-600 font-semibold hover:underline"
          >
            <RefreshCw className="w-3 h-3" /> Retry Comments
          </button>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && comments.length === 0 && (
        <div className="py-4 text-center text-xs text-surface-500">
          No comments yet. Be the first to start the discussion!
        </div>
      )}

      {/* Comments List (2 Levels) */}
      {!loading && !error && comments.length > 0 && (
        <div className="space-y-3">
          {comments.map((comment) => {
            const canDeleteRoot =
              currentUser?.id === comment.author.id || isPostAuthor;

            return (
              <div key={comment.id} className="space-y-2">
                {/* Level 1 Comment */}
                <div className="flex gap-2.5 items-start group">
                  <Avatar src={comment.author.avatar_url} alt={comment.author.full_name} size="sm" />
                  <div className="flex-1 min-w-0">
                    <div className="bg-surface-50 p-2.5 rounded-lg border border-surface-200">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-xs font-bold text-surface-900 truncate">
                          {comment.author.full_name}
                        </span>
                        <span className="text-[10px] text-surface-400 shrink-0">
                          {new Date(comment.created_at).toLocaleDateString([], {
                            month: 'short',
                            day: 'numeric',
                          })}
                        </span>
                      </div>
                      <p className="text-[10px] text-surface-500 line-clamp-1">{comment.author.headline}</p>
                      <p className="text-xs text-surface-800 mt-1 whitespace-pre-wrap">{comment.content}</p>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-3 mt-1 ml-2 text-[11px] text-surface-500">
                      <button
                        onClick={() =>
                          setReplyingToId(replyingToId === comment.id ? null : comment.id)
                        }
                        className="hover:text-brand-600 font-medium"
                      >
                        Reply
                      </button>
                      {canDeleteRoot && (
                        <button
                          onClick={() => handleDeleteComment(comment.id, false)}
                          className="hover:text-danger-600 flex items-center gap-1 opacity-80 hover:opacity-100"
                        >
                          <Trash2 className="w-3 h-3" /> Delete
                        </button>
                      )}
                    </div>

                    {/* Reply Input (Level 2 composer) */}
                    {replyingToId === comment.id && (
                      <div className="mt-2 flex gap-2 items-center pl-2">
                        <CornerDownRight className="w-3.5 h-3.5 text-surface-400 shrink-0" />
                        <input
                          type="text"
                          placeholder={`Reply to ${comment.author.full_name}...`}
                          value={replyText}
                          onChange={(e) => setReplyText(e.target.value)}
                          className="flex-1 text-xs rounded-md border border-surface-200 bg-white py-1 px-2.5 focus:outline-none focus:border-brand-600"
                          autoFocus
                        />
                        <Button
                          size="sm"
                          onClick={() => handleAddReply(comment.id)}
                          isLoading={submittingReply}
                          disabled={!replyText.trim()}
                        >
                          Reply
                        </Button>
                      </div>
                    )}

                    {/* Level 2 Replies */}
                    {comment.replies && comment.replies.length > 0 && (
                      <div className="mt-2 space-y-2 pl-4 border-l-2 border-surface-200">
                        {comment.replies.map((reply) => {
                          const canDeleteReply =
                            currentUser?.id === reply.author.id || isPostAuthor;

                          return (
                            <div key={reply.id} className="flex gap-2 items-start">
                              <Avatar src={reply.author.avatar_url} alt={reply.author.full_name} size="xs" />
                              <div className="flex-1 min-w-0">
                                <div className="bg-surface-50 p-2 rounded-lg border border-surface-200">
                                  <div className="flex items-center justify-between gap-1">
                                    <span className="text-xs font-semibold text-surface-900 truncate">
                                      {reply.author.full_name}
                                    </span>
                                    <span className="text-[10px] text-surface-400 shrink-0">
                                      {new Date(reply.created_at).toLocaleDateString([], {
                                        month: 'short',
                                        day: 'numeric',
                                      })}
                                    </span>
                                  </div>
                                  <p className="text-xs text-surface-800 mt-0.5 whitespace-pre-wrap">
                                    {reply.content}
                                  </p>
                                </div>
                                {canDeleteReply && (
                                  <button
                                    onClick={() => handleDeleteComment(reply.id, true, comment.id)}
                                    className="mt-0.5 ml-2 text-[10px] text-surface-400 hover:text-danger-600 flex items-center gap-1"
                                  >
                                    <Trash2 className="w-2.5 h-2.5" /> Delete
                                  </button>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
