import React, { useState } from 'react';
import { api } from '../../services/api';
import { PostDTO } from '../../types/api';
import { useAuthStore } from '../../stores/authStore';
import { useToastStore } from '../../stores/toastStore';
import { Modal } from '../../components/ui/Modal';
import { Button } from '../../components/ui/Button';
import { Avatar } from '../../components/ui/Avatar';
import { Code2, Image as ImageIcon, X } from 'lucide-react';

export interface PostComposerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (newPost: PostDTO) => void;
}

export const PostComposerModal: React.FC<PostComposerModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const { currentUser } = useAuthStore();
  const { addToast } = useToastStore();

  const [content, setContent] = useState('');
  const [showCode, setShowCode] = useState(false);
  const [codeLanguage, setCodeLanguage] = useState('python');
  const [codeSnippet, setCodeSnippet] = useState('');
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [isUploadingMedia, setIsUploadingMedia] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const MAX_CHARS = 3000;

  const handleMediaUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      addToast({
        type: 'error',
        title: 'File Too Large',
        message: 'Post images must be 5 MB or less.',
      });
      return;
    }

    setIsUploadingMedia(true);
    try {
      const res = await api.uploads.uploadPostMedia(file);
      setImageUrl(res.file_url);
      addToast({
        type: 'success',
        title: 'Image Attached',
        message: 'Post image uploaded successfully.',
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Upload Failed',
        message: err.message || 'Could not upload image.',
      });
    } finally {
      setIsUploadingMedia(false);
    }
  };

  const handleSubmit = async () => {
    if (!content.trim() && !codeSnippet.trim() && !imageUrl) {
      return;
    }

    setIsSubmitting(true);
    try {
      const post = await api.feed.createPost({
        content: content.trim(),
        code_snippet: showCode && codeSnippet.trim() ? codeSnippet.trim() : null,
        code_language: showCode && codeSnippet.trim() ? codeLanguage : null,
        image_url: imageUrl,
      });

      addToast({
        type: 'success',
        title: 'Post Published',
        message: 'Your update has been shared with your network.',
      });

      // Reset form
      setContent('');
      setShowCode(false);
      setCodeSnippet('');
      setImageUrl(null);

      onSuccess(post);
      onClose();
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Publish Failed',
        message: err.message || 'Could not publish post.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Create a Post"
      size="lg"
      footer={
        <div className="flex items-center justify-between w-full">
          {/* Action icons */}
          <div className="flex items-center gap-2">
            <label className="p-2 text-surface-500 hover:text-brand-600 hover:bg-surface-100 rounded-lg cursor-pointer transition-colors" title="Attach Image">
              <ImageIcon className="w-5 h-5" />
              <input
                type="file"
                accept="image/*"
                onChange={handleMediaUpload}
                disabled={isUploadingMedia || isSubmitting}
                className="hidden"
              />
            </label>

            <button
              type="button"
              onClick={() => setShowCode(!showCode)}
              className={`p-2 rounded-lg transition-colors ${
                showCode
                  ? 'text-brand-600 bg-brand-50'
                  : 'text-surface-500 hover:text-brand-600 hover:bg-surface-100'
              }`}
              title="Add Code Snippet"
            >
              <Code2 className="w-5 h-5" />
            </button>

            {isUploadingMedia && (
              <span className="text-xs text-brand-600 animate-pulse font-medium">
                Uploading image...
              </span>
            )}
          </div>

          <div className="flex items-center gap-3">
            <span
              className={`text-xs ${
                content.length > MAX_CHARS - 100 ? 'text-danger-600 font-bold' : 'text-surface-400'
              }`}
            >
              {content.length}/{MAX_CHARS}
            </span>
            <Button
              variant="secondary"
              size="sm"
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleSubmit}
              isLoading={isSubmitting}
              disabled={!content.trim() && !codeSnippet.trim() && !imageUrl}
            >
              Publish Post
            </Button>
          </div>
        </div>
      }
    >
      <div className="space-y-4">
        {/* Author badge */}
        <div className="flex items-center gap-3">
          <Avatar
            src={currentUser?.avatar_url || null}
            alt={currentUser?.full_name || 'Me'}
            size="md"
          />
          <div>
            <h4 className="text-sm font-bold text-surface-900">{currentUser?.full_name}</h4>
            <p className="text-xs text-surface-500 line-clamp-1">{currentUser?.headline}</p>
          </div>
        </div>

        {/* Content input */}
        <textarea
          rows={4}
          placeholder="What technical insight, architecture decision, or update do you want to share?"
          value={content}
          maxLength={MAX_CHARS}
          onChange={(e) => setContent(e.target.value)}
          className="w-full text-sm text-surface-900 placeholder:text-surface-400 border border-surface-200 rounded-lg p-3 focus:outline-none focus:border-brand-600 focus:ring-1 focus:ring-brand-600 resize-none"
          autoFocus
        />

        {/* Code Snippet Editor Section */}
        {showCode && (
          <div className="p-3 bg-surface-900 text-surface-100 rounded-lg space-y-2 border border-surface-700">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-surface-300">Code Snippet</span>
              <div className="flex items-center gap-2">
                <select
                  value={codeLanguage}
                  onChange={(e) => setCodeLanguage(e.target.value)}
                  className="bg-surface-800 text-surface-200 text-xs rounded border border-surface-700 px-2 py-1 focus:outline-none focus:border-brand-500"
                >
                  <option value="python">Python</option>
                  <option value="typescript">TypeScript</option>
                  <option value="sql">SQL</option>
                  <option value="bash">Bash</option>
                </select>
                <button
                  type="button"
                  onClick={() => {
                    setShowCode(false);
                    setCodeSnippet('');
                  }}
                  className="text-surface-400 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
            <textarea
              rows={4}
              placeholder="// Paste syntax-highlighted code here..."
              value={codeSnippet}
              onChange={(e) => setCodeSnippet(e.target.value)}
              className="w-full bg-surface-950 font-mono text-xs text-surface-200 p-2.5 rounded border border-surface-800 focus:outline-none focus:border-brand-500 resize-y"
            />
          </div>
        )}

        {/* Image Attachment Preview */}
        {imageUrl && (
          <div className="relative rounded-lg overflow-hidden border border-surface-200 max-h-60 bg-surface-100">
            <img src={imageUrl} alt="Post attachment" className="w-full h-auto object-cover max-h-60" />
            <button
              type="button"
              onClick={() => setImageUrl(null)}
              className="absolute top-2 right-2 p-1 bg-surface-900/70 hover:bg-surface-900 text-white rounded-full transition-colors"
              title="Remove image"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </Modal>
  );
};
