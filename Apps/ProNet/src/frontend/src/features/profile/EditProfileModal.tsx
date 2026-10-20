import React, { useState } from 'react';
import { api } from '../../services/api';
import { ProfileDetailDTO } from '../../types/api';
import { useAuthStore } from '../../stores/authStore';
import { useToastStore } from '../../stores/toastStore';
import { Modal } from '../../components/ui/Modal';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';

export interface EditProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  profile: ProfileDetailDTO;
  onSuccess: (updated: ProfileDetailDTO) => void;
}

export const EditProfileModal: React.FC<EditProfileModalProps> = ({
  isOpen,
  onClose,
  profile,
  onSuccess,
}) => {
  const { updateCurrentUserSummary } = useAuthStore();
  const { addToast } = useToastStore();

  const [headline, setHeadline] = useState(profile.profile.headline || '');
  const [bio, setBio] = useState(profile.profile.bio || '');
  const [location, setLocation] = useState(profile.profile.location || '');
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const updated = await api.users.updateProfile({
        headline: headline.trim(),
        bio: bio.trim() || null,
        location: location.trim(),
      });

      updateCurrentUserSummary({
        headline: updated.profile.headline,
      });

      addToast({
        type: 'success',
        title: 'Profile Updated',
        message: 'Your profile changes have been saved.',
      });

      onSuccess(updated);
      onClose();
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Save Failed',
        message: err.message || 'Could not update profile.',
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Edit Intro & Overview"
      size="md"
      footer={
        <>
          <Button variant="secondary" size="sm" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button variant="primary" size="sm" onClick={handleSubmit} isLoading={saving}>
            Save Changes
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Headline"
          value={headline}
          onChange={(e) => setHeadline(e.target.value)}
          placeholder="e.g. Staff AI Systems Engineer | Distributed LLM Training"
          required
        />

        <Input
          label="Location"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          placeholder="e.g. San Francisco, CA"
          required
        />

        <div>
          <label className="block text-sm font-medium text-surface-700 mb-1">
            About (Professional Summary)
          </label>
          <textarea
            rows={4}
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            placeholder="Share your engineering background, technical expertise, and career journey..."
            className="w-full text-sm rounded-md border border-surface-200 bg-white p-3 focus:outline-none focus:border-brand-600 focus:ring-1 focus:ring-brand-600 text-surface-900"
          />
        </div>
      </form>
    </Modal>
  );
};
