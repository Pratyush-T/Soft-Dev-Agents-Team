import React, { useState } from 'react';
import { api } from '../../services/api';
import { ProfileDetailDTO } from '../../types/api';
import { useAuthStore } from '../../stores/authStore';
import { useChatStore } from '../../stores/chatStore';
import { useToastStore } from '../../stores/toastStore';
import { Avatar } from '../../components/ui/Avatar';
import { DegreeBadge } from '../../components/ui/DegreeBadge';
import { Button } from '../../components/ui/Button';
import { Modal } from '../../components/ui/Modal';
import {
  Camera,
  Edit2,
  UserPlus,
  UserCheck,
  UserX,
  MessageSquare,
  Users,
  MapPin,
  Mail,
} from 'lucide-react';

export interface ProfileHeaderProps {
  profile: ProfileDetailDTO;
  isOwnProfile: boolean;
  onEditProfile: () => void;
  onMutualsClick: () => void;
  onProfileUpdated: (updated: ProfileDetailDTO) => void;
}

export const ProfileHeader: React.FC<ProfileHeaderProps> = ({
  profile,
  isOwnProfile,
  onEditProfile,
  onMutualsClick,
  onProfileUpdated,
}) => {
  const { updateCurrentUserSummary } = useAuthStore();
  const { openChatWithPeer } = useChatStore();
  const { addToast } = useToastStore();

  const [isUploadingAvatar, setIsUploadingAvatar] = useState(false);
  const [isActionPending, setIsActionPending] = useState(false);

  // Connect request modal with note
  const [isConnectModalOpen, setIsConnectModalOpen] = useState(false);
  const [connectNote, setConnectNote] = useState('');

  // Disconnect confirmation modal
  const [isDisconnectModalOpen, setIsDisconnectModalOpen] = useState(false);

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 2 * 1024 * 1024) {
      addToast({
        type: 'error',
        title: 'File Too Large',
        message: 'Avatar image must be 2 MB or less.',
      });
      return;
    }

    setIsUploadingAvatar(true);
    try {
      const res = await api.uploads.uploadAvatar(file);
      const updated = await api.users.updateProfile({ avatar_url: res.file_url });
      updateCurrentUserSummary({ avatar_url: res.file_url });
      onProfileUpdated(updated);
      addToast({
        type: 'success',
        title: 'Avatar Updated',
        message: 'Your profile picture has been updated.',
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Upload Failed',
        message: err.message || 'Could not upload avatar.',
      });
    } finally {
      setIsUploadingAvatar(false);
    }
  };

  const handleSendConnectionRequest = async () => {
    setIsActionPending(true);
    try {
      await api.connections.sendRequest({
        recipient_id: profile.id,
        note: connectNote.trim() || null,
      });

      // Update local view
      onProfileUpdated({
        ...profile,
        connection_status_with_viewer: 'PENDING',
        viewer_initiated_connection: true,
      });

      addToast({
        type: 'success',
        title: 'Invitation Sent',
        message: `Connection request sent to ${profile.full_name}.`,
      });
      setIsConnectModalOpen(false);
      setConnectNote('');
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Request Failed',
        message: err.message || 'Could not send connection request.',
      });
    } finally {
      setIsActionPending(false);
    }
  };

  const handleAcceptConnection = async () => {
    if (!profile.active_connection_id) return;
    setIsActionPending(true);
    try {
      await api.connections.acceptRequest(profile.active_connection_id);
      onProfileUpdated({
        ...profile,
        connection_status_with_viewer: 'ACCEPTED',
        degree: '1st',
        profile: {
          ...profile.profile,
          connections_count: profile.profile.connections_count + 1,
        },
      });
      addToast({
        type: 'success',
        title: 'Connected',
        message: `You are now directly connected with ${profile.full_name}!`,
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Accept Failed',
        message: err.message || 'Could not accept connection.',
      });
    } finally {
      setIsActionPending(false);
    }
  };

  const handleIgnoreConnection = async () => {
    if (!profile.active_connection_id) return;
    setIsActionPending(true);
    try {
      await api.connections.ignoreRequest(profile.active_connection_id);
      onProfileUpdated({
        ...profile,
        connection_status_with_viewer: 'NONE',
        active_connection_id: null,
      });
      addToast({
        type: 'info',
        title: 'Invitation Ignored',
        message: 'The invitation was ignored.',
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Action Failed',
        message: err.message || 'Could not ignore request.',
      });
    } finally {
      setIsActionPending(false);
    }
  };

  const handleWithdrawRequest = async () => {
    if (!profile.active_connection_id) return;
    setIsActionPending(true);
    try {
      await api.connections.withdrawRequest(profile.active_connection_id);
      onProfileUpdated({
        ...profile,
        connection_status_with_viewer: 'NONE',
        active_connection_id: null,
        viewer_initiated_connection: false,
      });
      addToast({
        type: 'info',
        title: 'Request Withdrawn',
        message: 'Your connection request was withdrawn.',
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Withdraw Failed',
        message: err.message || 'Could not withdraw request.',
      });
    } finally {
      setIsActionPending(false);
    }
  };

  const handleDisconnect = async () => {
    setIsActionPending(true);
    try {
      await api.connections.disconnect(profile.id);
      onProfileUpdated({
        ...profile,
        connection_status_with_viewer: 'NONE',
        degree: '2nd',
        active_connection_id: null,
        profile: {
          ...profile.profile,
          connections_count: Math.max(0, profile.profile.connections_count - 1),
        },
      });
      addToast({
        type: 'info',
        title: 'Disconnected',
        message: `Removed ${profile.full_name} from your connections.`,
      });
      setIsDisconnectModalOpen(false);
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Disconnect Failed',
        message: err.message || 'Could not remove connection.',
      });
    } finally {
      setIsActionPending(false);
    }
  };

  const handleStartMessage = () => {
    openChatWithPeer({
      id: profile.id,
      email: profile.email,
      full_name: profile.full_name,
      headline: profile.profile.headline,
      avatar_url: profile.profile.avatar_url,
    });
  };

  return (
    <div className="bg-white rounded-xl border border-surface-200 shadow-elevation-1 overflow-hidden">
      {/* Cover Banner */}
      <div className="h-36 sm:h-48 bg-gradient-to-r from-brand-800 via-brand-600 to-brand-500 relative" />

      {/* Profile Details Container */}
      <div className="px-5 sm:px-6 pb-6 relative">
        {/* Avatar with absolute positioning overlapping the banner */}
        <div className="flex justify-between items-end -mt-16 sm:-mt-20 mb-4">
          <div className="relative group">
            <Avatar
              src={profile.profile.avatar_url}
              alt={profile.full_name}
              size="xl"
              className="ring-4 ring-white shadow-elevation-2"
            />
            {isOwnProfile && (
              <label
                className="absolute inset-0 bg-surface-950/40 rounded-full flex items-center justify-center text-white opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer ring-4 ring-white"
                title="Change Profile Photo"
              >
                <Camera className="w-6 h-6" />
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={handleAvatarUpload}
                  disabled={isUploadingAvatar}
                  className="hidden"
                />
              </label>
            )}
          </div>

          {/* Action Buttons Toolbar */}
          <div className="flex items-center gap-2 pt-4">
            {isOwnProfile ? (
              <Button
                variant="outline"
                size="sm"
                onClick={onEditProfile}
                leftIcon={<Edit2 className="w-3.5 h-3.5" />}
              >
                Edit Profile
              </Button>
            ) : (
              <>
                {/* 1st Degree: Message & Disconnect */}
                {profile.degree === '1st' && (
                  <>
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={handleStartMessage}
                      leftIcon={<MessageSquare className="w-3.5 h-3.5" />}
                    >
                      Message
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setIsDisconnectModalOpen(true)}
                      leftIcon={<UserX className="w-3.5 h-3.5" />}
                    >
                      Disconnect
                    </Button>
                  </>
                )}

                {/* Incoming Pending Request: Accept / Ignore */}
                {profile.connection_status_with_viewer === 'PENDING' &&
                  !profile.viewer_initiated_connection && (
                    <>
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={handleAcceptConnection}
                        isLoading={isActionPending}
                        leftIcon={<UserCheck className="w-3.5 h-3.5" />}
                      >
                        Accept Request
                      </Button>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={handleIgnoreConnection}
                        disabled={isActionPending}
                      >
                        Ignore
                      </Button>
                    </>
                  )}

                {/* Outgoing Pending Request: Withdraw */}
                {profile.connection_status_with_viewer === 'PENDING' &&
                  profile.viewer_initiated_connection && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleWithdrawRequest}
                      isLoading={isActionPending}
                    >
                      Withdraw Request
                    </Button>
                  )}

                {/* No Edge (2nd or 3rd+): Connect */}
                {profile.connection_status_with_viewer === 'NONE' && profile.degree !== '1st' && (
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => setIsConnectModalOpen(true)}
                    leftIcon={<UserPlus className="w-3.5 h-3.5" />}
                  >
                    Connect
                  </Button>
                )}
              </>
            )}
          </div>
        </div>

        {/* Name & Headline & Degree */}
        <div className="space-y-1">
          <div className="flex items-center gap-2 flex-wrap">
            <h1 className="text-xl sm:text-2xl font-bold text-surface-900">
              {profile.full_name}
            </h1>
            {!isOwnProfile && <DegreeBadge degree={profile.degree} />}
          </div>

          <p className="text-sm font-medium text-surface-700 leading-snug">
            {profile.profile.headline}
          </p>

          <div className="flex items-center gap-4 text-xs text-surface-500 pt-1 flex-wrap">
            <span className="flex items-center gap-1">
              <MapPin className="w-3.5 h-3.5 text-surface-400" />
              {profile.profile.location}
            </span>
            <span className="flex items-center gap-1">
              <Mail className="w-3.5 h-3.5 text-surface-400" />
              {profile.email}
            </span>
          </div>

          {/* Social Graph Counts & Mutuals Link */}
          <div className="flex items-center gap-3 pt-2 text-xs">
            <span className="font-semibold text-brand-600">
              {profile.profile.connections_count}{' '}
              {profile.profile.connections_count === 1 ? 'connection' : 'connections'}
            </span>

            {!isOwnProfile && profile.mutual_connections_count > 0 && (
              <button
                onClick={onMutualsClick}
                className="flex items-center gap-1 text-surface-600 hover:text-brand-600 font-medium transition-colors"
              >
                <Users className="w-3.5 h-3.5 text-brand-600" />
                <span>
                  {profile.mutual_connections_count} mutual connection
                  {profile.mutual_connections_count === 1 ? '' : 's'}
                </span>
              </button>
            )}
          </div>
        </div>

        {/* Bio Narrative Section */}
        {profile.profile.bio && (
          <div className="mt-4 pt-4 border-t border-surface-100">
            <h3 className="text-xs font-bold text-surface-700 uppercase tracking-wider mb-1">
              About
            </h3>
            <p className="text-xs sm:text-sm text-surface-700 leading-relaxed whitespace-pre-wrap">
              {profile.profile.bio}
            </p>
          </div>
        )}
      </div>

      {/* Connect Request Modal with Note */}
      <Modal
        isOpen={isConnectModalOpen}
        onClose={() => setIsConnectModalOpen(false)}
        title={`Connect with ${profile.full_name}`}
        description="Include an optional personalized note to introduce yourself or mention mutual architectural interests."
        size="md"
        footer={
          <>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setIsConnectModalOpen(false)}
              disabled={isActionPending}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleSendConnectionRequest}
              isLoading={isActionPending}
            >
              Send Invitation
            </Button>
          </>
        }
      >
        <div className="space-y-3">
          <div className="flex items-center gap-3 p-3 bg-surface-50 rounded-lg border border-surface-200">
            <Avatar src={profile.profile.avatar_url} alt={profile.full_name} size="sm" />
            <div>
              <div className="text-xs font-bold text-surface-900">{profile.full_name}</div>
              <div className="text-[11px] text-surface-500 line-clamp-1">{profile.profile.headline}</div>
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-surface-700 mb-1">
              Personalized Note (Optional, max 300 characters)
            </label>
            <textarea
              rows={3}
              maxLength={300}
              value={connectNote}
              onChange={(e) => setConnectNote(e.target.value)}
              placeholder="Hi, I'd like to join your professional network on ProNet..."
              className="w-full text-xs rounded-md border border-surface-200 p-2.5 bg-white focus:outline-none focus:border-brand-600"
            />
            <div className="text-right text-[10px] text-surface-400 mt-0.5">
              {connectNote.length}/300
            </div>
          </div>
        </div>
      </Modal>

      {/* Disconnect Confirmation Modal */}
      <Modal
        isOpen={isDisconnectModalOpen}
        onClose={() => setIsDisconnectModalOpen(false)}
        title="Remove Connection"
        description={`Are you sure you want to disconnect from ${profile.full_name}?`}
        size="sm"
        footer={
          <>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setIsDisconnectModalOpen(false)}
              disabled={isActionPending}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              size="sm"
              onClick={handleDisconnect}
              isLoading={isActionPending}
            >
              Disconnect
            </Button>
          </>
        }
      >
        <p className="text-xs text-surface-600 leading-relaxed">
          Removing this connection will sever your 1st-degree edge. Direct messaging will be disabled until a new connection invitation is accepted.
        </p>
      </Modal>
    </div>
  );
};
