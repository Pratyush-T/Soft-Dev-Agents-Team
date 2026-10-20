import React, { useState, useEffect, useCallback } from 'react';
import { Modal } from '../../components/ui/Modal';
import { Button } from '../../components/ui/Button';
import { Avatar } from '../../components/ui/Avatar';
import { Badge } from '../../components/ui/Badge';
import { Skeleton } from '../../components/ui/Skeleton';
import { api } from '../../services/api';
import { useToastStore } from '../../stores/toastStore';
import { ApplicationStatus, JobApplicationDTO } from '../../types/api';
import {
  Users,
  FileText,
  Clock,
  ExternalLink,
  AlertTriangle,
  RefreshCw,
  Copy,
} from 'lucide-react';

export interface RecruiterPipelineModalProps {
  jobId: string;
  jobTitle: string;
  isOpen: boolean;
  onClose: () => void;
  onSelectApplicant?: (userId: string) => void;
}

const STAGES: { key: ApplicationStatus; label: string; color: 'brand' | 'warning' | 'success' | 'danger' }[] = [
  { key: 'APPLIED', label: 'Applied', color: 'brand' },
  { key: 'REVIEWING', label: 'Reviewing', color: 'warning' },
  { key: 'SHORTLISTED', label: 'Shortlisted', color: 'success' },
  { key: 'REJECTED', label: 'Rejected', color: 'danger' },
];

export const RecruiterPipelineModal: React.FC<RecruiterPipelineModalProps> = ({
  jobId,
  jobTitle,
  isOpen,
  onClose,
  onSelectApplicant,
}) => {
  const { addToast } = useToastStore();
  const [applications, setApplications] = useState<JobApplicationDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeStage, setActiveStage] = useState<ApplicationStatus | 'ALL'>('ALL');
  const [updatingAppId, setUpdatingAppId] = useState<string | null>(null);

  const fetchApplications = useCallback(async () => {
    if (!jobId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.jobs.getApplications(jobId);
      setApplications(data);
    } catch (err: any) {
      setError(err.message || 'Unable to retrieve applications for this requisition.');
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  useEffect(() => {
    if (isOpen) {
      fetchApplications();
    }
  }, [isOpen, fetchApplications]);

  const handleStatusChange = async (applicationId: string, newStatus: ApplicationStatus) => {
    setUpdatingAppId(applicationId);
    try {
      const updated = await api.jobs.updateApplicationStatus(jobId, applicationId, {
        status: newStatus,
      });
      setApplications((prev) =>
        prev.map((app) => (app.id === applicationId ? updated : app))
      );
      addToast({
        type: 'success',
        title: 'Stage Updated',
        message: `Candidate moved to ${newStatus}.`,
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Update Failed',
        message: err.message || 'Unable to change candidate status.',
      });
    } finally {
      setUpdatingAppId(null);
    }
  };

  const handleCopyLink = () => {
    navigator.clipboard.writeText(window.location.href);
    addToast({
      type: 'info',
      title: 'Link Copied',
      message: 'Job link copied to clipboard.',
    });
  };

  const filteredApps =
    activeStage === 'ALL'
      ? applications
      : applications.filter((app) => app.status === activeStage);

  const stageCounts = applications.reduce((acc, app) => {
    acc[app.status] = (acc[app.status] || 0) + 1;
    return acc;
  }, {} as Record<ApplicationStatus, number>);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Candidate Pipeline & ATS"
      description={`Requisition: ${jobTitle} (${applications.length} total applicant${
        applications.length === 1 ? '' : 's'
      })`}
      size="xl"
      footer={
        <div className="flex items-center justify-between w-full">
          <Button
            variant="outline"
            size="sm"
            onClick={handleCopyLink}
            leftIcon={<Copy className="w-3.5 h-3.5" />}
          >
            Copy Job Share Link
          </Button>
          <Button variant="secondary" size="sm" onClick={onClose}>
            Close Pipeline
          </Button>
        </div>
      }
    >
      <div className="space-y-4">
        {/* Stage Filter Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 border-b border-surface-200 text-xs">
          <button
            onClick={() => setActiveStage('ALL')}
            className={`px-3 py-1.5 rounded-lg font-semibold transition-colors shrink-0 ${
              activeStage === 'ALL'
                ? 'bg-surface-900 text-white'
                : 'text-surface-600 hover:bg-surface-100'
            }`}
          >
            All Stages ({applications.length})
          </button>
          {STAGES.map((s) => (
            <button
              key={s.key}
              onClick={() => setActiveStage(s.key)}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-colors flex items-center gap-1.5 shrink-0 ${
                activeStage === s.key
                  ? 'bg-brand-600 text-white'
                  : 'text-surface-600 hover:bg-surface-100'
              }`}
            >
              <span>{s.label}</span>
              <span
                className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ${
                  activeStage === s.key ? 'bg-white/20 text-white' : 'bg-surface-200 text-surface-700'
                }`}
              >
                {stageCounts[s.key] || 0}
              </span>
            </button>
          ))}
        </div>

        {/* 1. Loading Skeleton */}
        {loading && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="p-4 rounded-xl border border-surface-200 bg-white space-y-3">
                <div className="flex items-center gap-3">
                  <Skeleton variant="circular" width={40} height={40} />
                  <div className="flex-1 space-y-1.5">
                    <Skeleton width="30%" height={14} />
                    <Skeleton width="60%" height={12} />
                  </div>
                </div>
                <Skeleton width="100%" height={12} />
              </div>
            ))}
          </div>
        )}

        {/* 2. Error State */}
        {!loading && error && (
          <div className="p-8 text-center bg-danger-50/50 rounded-xl border border-danger-200 space-y-3">
            <AlertTriangle className="w-8 h-8 text-danger-600 mx-auto" />
            <h4 className="text-sm font-bold text-surface-900">Access Restricted / Error</h4>
            <p className="text-xs text-surface-600 max-w-sm mx-auto">{error}</p>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchApplications}
              leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
            >
              Retry
            </Button>
          </div>
        )}

        {/* 3. Empty State */}
        {!loading && !error && filteredApps.length === 0 && (
          <div className="p-10 text-center bg-surface-50 rounded-xl border border-surface-200 space-y-3">
            <Users className="w-10 h-10 text-surface-400 mx-auto" />
            <h4 className="text-sm font-bold text-surface-900">No Candidates in This Stage</h4>
            <p className="text-xs text-surface-500 max-w-sm mx-auto">
              Candidates who apply to this role will appear here automatically for review and pipeline staging.
            </p>
          </div>
        )}

        {/* 4. Populated Candidate List */}
        {!loading && !error && filteredApps.length > 0 && (
          <div className="space-y-3 max-h-[55vh] overflow-y-auto pr-1">
            {filteredApps.map((app) => (
              <div
                key={app.id}
                className="p-4 rounded-xl border border-surface-200 bg-white hover:border-brand-300 transition-all shadow-sm space-y-3"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  {/* Candidate Info */}
                  <div className="flex items-start gap-3">
                    <Avatar
                      src={app.applicant.avatar_url}
                      alt={app.applicant.full_name}
                      size="md"
                    />
                    <div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => onSelectApplicant?.(app.applicant.id)}
                          className="font-bold text-surface-900 hover:text-brand-600 text-sm text-left"
                        >
                          {app.applicant.full_name}
                        </button>
                        <Badge
                          variant={
                            app.status === 'SHORTLISTED'
                              ? 'success'
                              : app.status === 'REVIEWING'
                              ? 'warning'
                              : app.status === 'REJECTED'
                              ? 'danger'
                              : 'brand'
                          }
                          size="sm"
                        >
                          {app.status}
                        </Badge>
                      </div>
                      <p className="text-xs text-surface-600 line-clamp-1 mt-0.5">
                        {app.profile_headline_snapshot || app.applicant.headline}
                      </p>
                      <div className="flex items-center gap-2 text-[11px] text-surface-400 mt-1">
                        <Clock className="w-3 h-3" />
                        <span>Applied {new Date(app.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>

                  {/* Stage Transition Selector */}
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-[11px] text-surface-500 font-medium">Stage:</span>
                    <select
                      value={app.status}
                      disabled={updatingAppId === app.id}
                      onChange={(e) =>
                        handleStatusChange(app.id, e.target.value as ApplicationStatus)
                      }
                      className="text-xs rounded-md border border-surface-200 bg-surface-50 py-1 px-2.5 text-surface-800 font-semibold focus:outline-none focus:border-brand-600 cursor-pointer"
                    >
                      <option value="APPLIED">Applied</option>
                      <option value="REVIEWING">Reviewing</option>
                      <option value="SHORTLISTED">Shortlisted</option>
                      <option value="REJECTED">Rejected</option>
                    </select>
                  </div>
                </div>

                {/* Candidate Skills Snapshot */}
                {app.skills_snapshot && app.skills_snapshot.length > 0 && (
                  <div className="flex items-center gap-1.5 flex-wrap pt-1">
                    <span className="text-[11px] text-surface-500">Skills:</span>
                    {app.skills_snapshot.map((skill) => (
                      <span
                        key={skill}
                        className="text-[10px] bg-surface-100 text-surface-700 px-2 py-0.5 rounded border border-surface-200"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                )}

                {/* Cover Note Bubble */}
                {app.cover_note && (
                  <div className="p-2.5 rounded-lg bg-surface-50 text-xs text-surface-700 border border-surface-100 italic leading-relaxed">
                    &ldquo;{app.cover_note}&rdquo;
                  </div>
                )}

                {/* Resume Link */}
                {app.resume_url && (
                  <div className="pt-1">
                    <a
                      href={app.resume_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 text-xs text-brand-600 hover:text-brand-700 font-semibold hover:underline"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      <span>View Attached Candidate Resume</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </Modal>
  );
};
