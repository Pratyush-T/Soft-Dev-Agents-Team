import React, { useState } from 'react';
import { Modal } from '../../components/ui/Modal';
import { Button } from '../../components/ui/Button';
import { Avatar } from '../../components/ui/Avatar';
import { api } from '../../services/api';
import { useAuthStore } from '../../stores/authStore';
import { useToastStore } from '../../stores/toastStore';
import { JobApplicationDTO, JobDTO } from '../../types/api';
import { UploadCloud, CheckCircle2, FileText } from 'lucide-react';

export interface EasyApplyModalProps {
  job: JobDTO;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (application: JobApplicationDTO) => void;
}

export const EasyApplyModal: React.FC<EasyApplyModalProps> = ({
  job,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const { currentUser } = useAuthStore();
  const { addToast } = useToastStore();

  const [coverNote, setCoverNote] = useState('');
  const [resumeUrl, setResumeUrl] = useState<string | null>(null);
  const [resumeFileName, setResumeFileName] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 10 * 1024 * 1024) {
      addToast({
        type: 'warning',
        title: 'File Too Large',
        message: 'Resume size must be less than 10MB.',
      });
      return;
    }

    setIsUploading(true);
    try {
      const res = await api.uploads.uploadResume(file);
      setResumeUrl(res.file_url);
      setResumeFileName(file.name);
      addToast({
        type: 'success',
        title: 'Resume Attached',
        message: `Attached ${file.name}`,
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Upload Failed',
        message: err.message || 'Unable to upload resume document.',
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const application = await api.jobs.apply(job.id, {
        cover_note: coverNote.trim() || undefined,
        resume_url: resumeUrl || undefined,
      });

      addToast({
        type: 'success',
        title: 'Application Submitted!',
        message: `You applied to ${job.title} at ${job.company_name}.`,
      });

      onSuccess(application);
      onClose();
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Application Failed',
        message: err.message || 'Could not submit your application.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Easy Apply to ${job.company_name}`}
      description={`${job.title} • ${job.location}`}
      size="md"
      footer={
        <>
          <Button variant="ghost" size="sm" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleSubmit}
            isLoading={isSubmitting}
          >
            Submit Application
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4 text-xs">
        {/* Applicant Snapshot Preview */}
        <div className="bg-surface-50 p-3.5 rounded-lg border border-surface-200">
          <div className="text-[11px] font-bold text-surface-500 uppercase tracking-wider mb-2">
            Applicant Profile Snapshot
          </div>
          <div className="flex items-center gap-3">
            <Avatar
              src={currentUser?.avatar_url || null}
              alt={currentUser?.full_name || 'Applicant'}
              size="md"
            />
            <div className="min-w-0">
              <div className="font-bold text-surface-900 text-sm">
                {currentUser?.full_name || 'Current User'}
              </div>
              <div className="text-surface-600 text-xs line-clamp-1">
                {currentUser?.headline || 'ProNet Member'}
              </div>
              <div className="text-surface-400 text-[11px] mt-0.5">
                {currentUser?.email}
              </div>
            </div>
          </div>
        </div>

        {/* Cover Note */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="font-medium text-surface-700">
              Cover Note (Optional)
            </label>
            <span className="text-[11px] text-surface-400">
              {coverNote.length}/500
            </span>
          </div>
          <textarea
            rows={4}
            maxLength={500}
            placeholder="Introduce yourself, your key architectural projects, and why you're a great fit for this team..."
            value={coverNote}
            onChange={(e) => setCoverNote(e.target.value)}
            className="w-full text-xs rounded-md border border-surface-200 bg-white p-2.5 text-surface-900 focus:outline-none focus:border-brand-600 shadow-sm leading-relaxed"
          />
        </div>

        {/* Resume Attachment Dropzone */}
        <div>
          <label className="block font-medium text-surface-700 mb-1">
            Attach Resume (PDF, DOCX, or TXT)
          </label>
          <div className="border-2 border-dashed border-surface-200 hover:border-brand-300 rounded-lg p-4 text-center bg-surface-50/50 transition-colors">
            {resumeFileName ? (
              <div className="flex items-center justify-center gap-2 text-emerald-700 font-semibold text-xs">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span className="truncate max-w-xs">{resumeFileName}</span>
                <button
                  type="button"
                  onClick={() => {
                    setResumeUrl(null);
                    setResumeFileName(null);
                  }}
                  className="text-surface-400 hover:text-danger-600 text-xs ml-1"
                >
                  Remove
                </button>
              </div>
            ) : (
              <label className="cursor-pointer flex flex-col items-center">
                <UploadCloud className="w-8 h-8 text-surface-400 mb-1.5" />
                <span className="text-xs font-semibold text-brand-600 hover:underline">
                  {isUploading ? 'Uploading document...' : 'Click to upload your resume'}
                </span>
                <span className="text-[10px] text-surface-400 mt-0.5">
                  Max file size: 10 MB
                </span>
                <input
                  type="file"
                  accept=".pdf,.doc,.docx,.txt"
                  onChange={handleFileUpload}
                  disabled={isUploading}
                  className="hidden"
                />
              </label>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 text-[11px] text-surface-500 pt-1">
          <FileText className="w-3.5 h-3.5 text-brand-600 shrink-0" />
          <span>Your ProNet career profile and skills are included automatically with your submission.</span>
        </div>
      </form>
    </Modal>
  );
};
