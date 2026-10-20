import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../../services/api';
import { EducationDTO, ExperienceDTO, ProfileDetailDTO } from '../../types/api';
import { useAuthStore } from '../../stores/authStore';
import { useToastStore } from '../../stores/toastStore';
import { ProfileHeader } from './ProfileHeader';
import { ExperienceTimeline } from './ExperienceTimeline';
import { EducationTimeline } from './EducationTimeline';
import { SkillsCard } from './SkillsCard';
import { MutualConnectionsModal } from './MutualConnectionsModal';
import { EditProfileModal } from './EditProfileModal';
import { ExperienceModal } from './ExperienceModal';
import { EducationModal } from './EducationModal';
import { Skeleton } from '../../components/ui/Skeleton';
import { Button } from '../../components/ui/Button';
import { AlertCircle, RefreshCw, ArrowLeft } from 'lucide-react';

export interface ProfileViewProps {
  userId: string;
  onSelectUser?: (userId: string) => void;
  onBackToFeed?: () => void;
}

export const ProfileView: React.FC<ProfileViewProps> = ({
  userId,
  onSelectUser,
  onBackToFeed,
}) => {
  const { currentUser } = useAuthStore();
  const { addToast } = useToastStore();

  const [profile, setProfile] = useState<ProfileDetailDTO | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modals state
  const [isEditProfileOpen, setIsEditProfileOpen] = useState(false);
  const [isMutualsOpen, setIsMutualsOpen] = useState(false);

  // Experience modal state
  const [isExpModalOpen, setIsExpModalOpen] = useState(false);
  const [selectedExp, setSelectedExp] = useState<ExperienceDTO | null>(null);

  // Education modal state
  const [isEduModalOpen, setIsEduModalOpen] = useState(false);
  const [selectedEdu, setSelectedEdu] = useState<EducationDTO | null>(null);

  const isOwnProfile = currentUser?.id === userId;

  const fetchProfile = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.users.getProfile(userId);
      setProfile(data);
    } catch (err: any) {
      setError(err.message || 'User profile could not be retrieved.');
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  // Experience CRUD handlers
  const handleAddExp = () => {
    setSelectedExp(null);
    setIsExpModalOpen(true);
  };

  const handleEditExp = (exp: ExperienceDTO) => {
    setSelectedExp(exp);
    setIsExpModalOpen(true);
  };

  const handleDeleteExp = async (expId: string) => {
    if (!window.confirm('Delete this experience position?')) return;
    try {
      await api.users.deleteExperience(expId);
      addToast({
        type: 'info',
        title: 'Removed',
        message: 'Experience entry deleted.',
      });
      fetchProfile();
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Delete Failed',
        message: err.message || 'Could not delete position.',
      });
    }
  };

  // Education CRUD handlers
  const handleAddEdu = () => {
    setSelectedEdu(null);
    setIsEduModalOpen(true);
  };

  const handleEditEdu = (edu: EducationDTO) => {
    setSelectedEdu(edu);
    setIsEduModalOpen(true);
  };

  const handleDeleteEdu = async (eduId: string) => {
    if (!window.confirm('Delete this education entry?')) return;
    try {
      await api.users.deleteEducation(eduId);
      addToast({
        type: 'info',
        title: 'Removed',
        message: 'Education entry deleted.',
      });
      fetchProfile();
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Delete Failed',
        message: err.message || 'Could not delete education record.',
      });
    }
  };

  // Skill Add & Remove
  const handleAddSkill = async (skillName: string) => {
    try {
      const newSkill = await api.users.addSkill(skillName);
      if (profile) {
        setProfile({
          ...profile,
          skills: [...profile.skills, newSkill],
        });
      }
      addToast({
        type: 'success',
        title: 'Skill Added',
        message: `Added ${skillName} to your profile.`,
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Failed',
        message: err.message || 'Could not add skill.',
      });
    }
  };

  const handleRemoveSkill = async (skillId: string) => {
    try {
      await api.users.removeSkill(skillId);
      if (profile) {
        setProfile({
          ...profile,
          skills: profile.skills.filter((s) => s.id !== skillId),
        });
      }
      addToast({
        type: 'info',
        title: 'Skill Removed',
        message: 'Skill removed from profile.',
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Failed',
        message: err.message || 'Could not remove skill.',
      });
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
      {/* 1. Loading Skeleton */}
      {loading && (
        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-surface-200 overflow-hidden">
            <Skeleton height={144} width="100%" />
            <div className="px-6 pb-6 -mt-16 space-y-3">
              <Skeleton variant="circular" width={72} height={72} className="ring-4 ring-white" />
              <Skeleton width="40%" height={24} />
              <Skeleton width="60%" height={16} />
              <Skeleton width="30%" height={14} />
            </div>
          </div>
          <div className="bg-white rounded-xl border border-surface-200 p-6 space-y-4">
            <Skeleton width="30%" height={20} />
            <Skeleton width="100%" height={60} />
            <Skeleton width="100%" height={60} />
          </div>
        </div>
      )}

      {/* 2. Error State with Retry */}
      {!loading && error && (
        <div className="bg-white rounded-xl border border-danger-200 p-10 text-center space-y-4 shadow-elevation-1">
          <div className="w-12 h-12 bg-danger-50 rounded-full flex items-center justify-center mx-auto text-danger-600">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-surface-900">User Profile Not Found</h3>
            <p className="text-xs text-surface-600 mt-1 max-w-sm mx-auto">{error}</p>
          </div>
          <div className="flex items-center justify-center gap-3 pt-2">
            {onBackToFeed && (
              <Button variant="outline" size="sm" onClick={onBackToFeed} leftIcon={<ArrowLeft className="w-4 h-4" />}>
                Return to Feed
              </Button>
            )}
            <Button variant="primary" size="sm" onClick={fetchProfile} leftIcon={<RefreshCw className="w-4 h-4" />}>
              Retry Request
            </Button>
          </div>
        </div>
      )}

      {/* 3. Populated View */}
      {!loading && !error && profile && (
        <>
          {/* Header */}
          <ProfileHeader
            profile={profile}
            isOwnProfile={isOwnProfile}
            onEditProfile={() => setIsEditProfileOpen(true)}
            onMutualsClick={() => setIsMutualsOpen(true)}
            onProfileUpdated={(updated) => setProfile(updated)}
          />

          {/* Experience Timeline */}
          <ExperienceTimeline
            experiences={profile.experiences}
            isOwnProfile={isOwnProfile}
            onAdd={handleAddExp}
            onEdit={handleEditExp}
            onDelete={handleDeleteExp}
          />

          {/* Education Timeline */}
          <EducationTimeline
            educations={profile.educations}
            isOwnProfile={isOwnProfile}
            onAdd={handleAddEdu}
            onEdit={handleEditEdu}
            onDelete={handleDeleteEdu}
          />

          {/* Skills Card */}
          <SkillsCard
            skills={profile.skills}
            isOwnProfile={isOwnProfile}
            onAddSkill={handleAddSkill}
            onRemoveSkill={handleRemoveSkill}
          />

          {/* Mutual Connections Modal */}
          <MutualConnectionsModal
            isOpen={isMutualsOpen}
            onClose={() => setIsMutualsOpen(false)}
            userId={profile.id}
            userName={profile.full_name}
            onSelectUser={onSelectUser}
          />

          {/* Edit Profile Modal */}
          <EditProfileModal
            isOpen={isEditProfileOpen}
            onClose={() => setIsEditProfileOpen(false)}
            profile={profile}
            onSuccess={(updated) => setProfile(updated)}
          />

          {/* Add / Edit Experience Modal */}
          <ExperienceModal
            isOpen={isExpModalOpen}
            onClose={() => setIsExpModalOpen(false)}
            initialData={selectedExp}
            onSuccess={fetchProfile}
          />

          {/* Add / Edit Education Modal */}
          <EducationModal
            isOpen={isEduModalOpen}
            onClose={() => setIsEduModalOpen(false)}
            initialData={selectedEdu}
            onSuccess={fetchProfile}
          />
        </>
      )}
    </div>
  );
};
