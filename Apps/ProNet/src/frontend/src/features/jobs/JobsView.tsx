import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../../services/api';
import { JobDTO, JobFilterParams, JobApplicationDTO, JobStatus } from '../../types/api';
import { useAuthStore } from '../../stores/authStore';
import { useToastStore } from '../../stores/toastStore';
import { JobSearchFilterBar } from './JobSearchFilterBar';
import { CreateJobModal } from './CreateJobModal';
import { EasyApplyModal } from './EasyApplyModal';
import { RecruiterPipelineModal } from './RecruiterPipelineModal';
import { Avatar } from '../../components/ui/Avatar';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Skeleton } from '../../components/ui/Skeleton';
import {
  Briefcase,
  MapPin,
  DollarSign,
  Clock,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Building,
  Users,
  Send,
  FileCheck,
  ExternalLink,
} from 'lucide-react';

export interface JobsViewProps {
  onSelectUser?: (userId: string) => void;
}

export const JobsView: React.FC<JobsViewProps> = ({ onSelectUser }) => {
  const { currentUser } = useAuthStore();
  const { addToast } = useToastStore();

  const [activeTab, setActiveTab] = useState<'browse' | 'my-applications'>('browse');

  // Browse state
  const [jobs, setJobs] = useState<JobDTO[]>([]);
  const [selectedJob, setSelectedJob] = useState<JobDTO | null>(null);
  const [filters, setFilters] = useState<JobFilterParams>({});
  const [loadingJobs, setLoadingJobs] = useState(true);
  const [jobsError, setJobsError] = useState<string | null>(null);

  // My applications state
  const [myApplications, setMyApplications] = useState<JobApplicationDTO[]>([]);
  const [loadingApps, setLoadingApps] = useState(false);
  const [appsError, setAppsError] = useState<string | null>(null);

  // Modals state
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isApplyOpen, setIsApplyOpen] = useState(false);
  const [isAtsOpen, setIsAtsOpen] = useState(false);

  // Fetch Jobs
  const fetchJobs = useCallback(async (params: JobFilterParams) => {
    setLoadingJobs(true);
    setJobsError(null);
    try {
      const data = await api.jobs.getJobs(params);
      setJobs(data.items);
      // Select first job if none selected or current selection not in list
      if (data.items.length > 0) {
        setSelectedJob((prev) => {
          if (prev && data.items.some((j) => j.id === prev.id)) {
            return data.items.find((j) => j.id === prev.id) || data.items[0];
          }
          return data.items[0];
        });
      } else {
        setSelectedJob(null);
      }
    } catch (err: any) {
      setJobsError(err.message || 'Unable to retrieve job requisitions.');
    } finally {
      setLoadingJobs(false);
    }
  }, []);

  // Fetch My Applications
  const fetchMyApplications = useCallback(async () => {
    setLoadingApps(true);
    setAppsError(null);
    try {
      const data = await api.jobs.getMyApplications();
      setMyApplications(data);
    } catch (err: any) {
      setAppsError(err.message || 'Unable to load your job applications.');
    } finally {
      setLoadingApps(false);
    }
  }, []);

  useEffect(() => {
    if (activeTab === 'browse') {
      fetchJobs(filters);
    } else {
      fetchMyApplications();
    }
  }, [activeTab, filters, fetchJobs, fetchMyApplications]);

  const handleJobCreated = (newJob: JobDTO) => {
    setJobs((prev) => [newJob, ...prev]);
    setSelectedJob(newJob);
  };

  const handleApplicationSuccess = (application: JobApplicationDTO) => {
    // Update selected job applied state
    if (selectedJob && selectedJob.id === application.job_id) {
      const updated = {
        ...selectedJob,
        has_viewer_applied: true,
        viewer_application_status: application.status,
        application_count: selectedJob.application_count + 1,
      };
      setSelectedJob(updated);
      setJobs((prev) => prev.map((j) => (j.id === updated.id ? updated : j)));
    }
  };

  const handleToggleJobStatus = async (job: JobDTO) => {
    const nextStatus: JobStatus = job.status === 'OPEN' ? 'CLOSED' : 'OPEN';
    try {
      const updated = await api.jobs.updateJobStatus(job.id, nextStatus);
      setSelectedJob(updated);
      setJobs((prev) => prev.map((j) => (j.id === updated.id ? updated : j)));
      addToast({
        type: 'info',
        title: 'Status Updated',
        message: `Job is now ${nextStatus}.`,
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Update Failed',
        message: err.message || 'Could not update status.',
      });
    }
  };

  const formatSalary = (min: number, max: number) => {
    const formatK = (val: number) => `$${Math.round(val / 1000)}k`;
    return `${formatK(min)} - ${formatK(max)} / yr`;
  };

  const isOwnerOfSelected = currentUser && selectedJob && currentUser.id === selectedJob.poster.id;

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-4">
      {/* Top Header & Sub-Navigation */}
      <div className="bg-white rounded-xl border border-surface-200 shadow-elevation-1 p-2 sm:p-3">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          {/* Tabs */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab('browse')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
                activeTab === 'browse'
                  ? 'bg-brand-600 text-white shadow-sm'
                  : 'text-surface-600 hover:text-surface-900 hover:bg-surface-100'
              }`}
            >
              <Briefcase className="w-4 h-4" />
              <span>Explore Jobs</span>
            </button>

            <button
              onClick={() => setActiveTab('my-applications')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
                activeTab === 'my-applications'
                  ? 'bg-brand-600 text-white shadow-sm'
                  : 'text-surface-600 hover:text-surface-900 hover:bg-surface-100'
              }`}
            >
              <FileCheck className="w-4 h-4" />
              <span>My Applications</span>
              {myApplications.length > 0 && (
                <span
                  className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ${
                    activeTab === 'my-applications'
                      ? 'bg-white text-brand-700'
                      : 'bg-surface-200 text-surface-700'
                  }`}
                >
                  {myApplications.length}
                </span>
              )}
            </button>
          </div>

          {/* Post Job Trigger */}
          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsCreateOpen(true)}
            leftIcon={<Briefcase className="w-4 h-4" />}
          >
            Post a Job
          </Button>
        </div>
      </div>

      {/* VIEW: BROWSE JOBS */}
      {activeTab === 'browse' && (
        <div className="space-y-4">
          {/* Search & Filter Bar */}
          <JobSearchFilterBar
            filters={filters}
            onChange={(newFilters) => setFilters(newFilters)}
            onPostJobClick={() => setIsCreateOpen(true)}
          />

          {/* 1. Loading Skeleton */}
          {loadingJobs && (
            <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
              <div className="md:col-span-5 space-y-3">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="bg-white rounded-xl border border-surface-200 p-4 space-y-3">
                    <Skeleton width="60%" height={16} />
                    <Skeleton width="40%" height={12} />
                    <Skeleton width="80%" height={12} />
                  </div>
                ))}
              </div>
              <div className="md:col-span-7 bg-white rounded-xl border border-surface-200 p-6 space-y-4">
                <Skeleton width="50%" height={24} />
                <Skeleton width="30%" height={16} />
                <Skeleton width="100%" height={150} />
              </div>
            </div>
          )}

          {/* 2. Error State */}
          {!loadingJobs && jobsError && (
            <div className="bg-white rounded-xl border border-danger-200 p-8 text-center space-y-3 shadow-elevation-1">
              <AlertTriangle className="w-10 h-10 text-danger-600 mx-auto" />
              <h3 className="text-base font-bold text-surface-900">Failed to Load Job Requisitions</h3>
              <p className="text-xs text-surface-600 max-w-sm mx-auto">{jobsError}</p>
              <Button
                variant="primary"
                size="sm"
                onClick={() => fetchJobs(filters)}
                leftIcon={<RefreshCw className="w-4 h-4" />}
              >
                Retry
              </Button>
            </div>
          )}

          {/* 3. Empty State */}
          {!loadingJobs && !jobsError && jobs.length === 0 && (
            <div className="bg-white rounded-xl border border-surface-200 p-12 text-center space-y-3 shadow-elevation-1">
              <div className="w-12 h-12 bg-brand-50 rounded-full flex items-center justify-center mx-auto text-brand-600">
                <Briefcase className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-surface-900">No Jobs Match Your Filters</h3>
              <p className="text-xs text-surface-500 max-w-sm mx-auto">
                Try broadening your search keywords, workplace type (Remote/Hybrid), or clear active filters.
              </p>
              <div className="flex justify-center gap-3 pt-2">
                <Button variant="outline" size="sm" onClick={() => setFilters({})}>
                  Clear All Filters
                </Button>
                <Button variant="primary" size="sm" onClick={() => setIsCreateOpen(true)}>
                  Post the First Job
                </Button>
              </div>
            </div>
          )}

          {/* 4. Populated Split View */}
          {!loadingJobs && !jobsError && jobs.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-start">
              {/* Left Column: Job Cards List */}
              <div className="md:col-span-5 space-y-3 max-h-[calc(100vh-14rem)] overflow-y-auto pr-1">
                {jobs.map((job) => {
                  const isSelected = selectedJob?.id === job.id;
                  return (
                    <div
                      key={job.id}
                      onClick={() => setSelectedJob(job)}
                      className={`p-4 rounded-xl border transition-all cursor-pointer bg-white ${
                        isSelected
                          ? 'border-brand-600 ring-2 ring-brand-100 shadow-sm'
                          : 'border-surface-200 hover:border-brand-300 shadow-elevation-1'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <h4 className="text-xs font-bold text-surface-900 hover:text-brand-600 line-clamp-1">
                            {job.title}
                          </h4>
                          <div className="flex items-center gap-1.5 text-xs text-surface-600 mt-0.5">
                            <Building className="w-3.5 h-3.5 text-surface-400 shrink-0" />
                            <span className="font-medium">{job.company_name}</span>
                          </div>
                        </div>

                        <Badge
                          variant={job.status === 'OPEN' ? 'success' : 'default'}
                          size="sm"
                        >
                          {job.status}
                        </Badge>
                      </div>

                      <div className="flex items-center gap-2 text-[11px] text-surface-500 mt-2">
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3 h-3 text-surface-400" />
                          {job.location}
                        </span>
                        <span>•</span>
                        <span className="bg-surface-100 px-1.5 py-0.2 rounded text-[10px] font-semibold text-surface-700">
                          {job.workplace_type}
                        </span>
                      </div>

                      <div className="flex items-center justify-between mt-3 pt-2.5 border-t border-surface-100 text-xs">
                        <span className="font-semibold text-surface-800">
                          {formatSalary(job.salary_min, job.salary_max)}
                        </span>

                        {job.has_viewer_applied ? (
                          <span className="flex items-center gap-1 text-[11px] font-bold text-brand-600">
                            <CheckCircle2 className="w-3.5 h-3.5 text-brand-600" />
                            Applied
                          </span>
                        ) : (
                          <span className="text-[11px] text-surface-400">
                            {job.application_count} applicants
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Right Column: Selected Job Details Sticky Pane */}
              <div className="md:col-span-7 bg-white rounded-xl border border-surface-200 shadow-elevation-1 p-6 sticky top-20">
                {selectedJob ? (
                  <div className="space-y-6">
                    {/* Header */}
                    <div className="border-b border-surface-100 pb-5">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <h2 className="text-xl font-bold text-surface-900 tracking-tight">
                            {selectedJob.title}
                          </h2>
                          <div className="flex items-center gap-2 text-sm text-surface-700 mt-1">
                            <span className="font-semibold text-brand-700">
                              {selectedJob.company_name}
                            </span>
                            <span>•</span>
                            <span className="text-surface-500">{selectedJob.location}</span>
                            <span>•</span>
                            <Badge variant="brand" size="sm">
                              {selectedJob.workplace_type}
                            </Badge>
                          </div>
                        </div>

                        <Badge
                          variant={selectedJob.status === 'OPEN' ? 'success' : 'default'}
                          size="md"
                        >
                          {selectedJob.status}
                        </Badge>
                      </div>

                      <div className="flex items-center gap-6 mt-4 text-xs text-surface-600">
                        <div className="flex items-center gap-1.5 font-bold text-surface-900 text-sm">
                          <DollarSign className="w-4 h-4 text-emerald-600" />
                          <span>{formatSalary(selectedJob.salary_min, selectedJob.salary_max)}</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <Users className="w-4 h-4 text-surface-400" />
                          <span>{selectedJob.application_count} applicants</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <Clock className="w-4 h-4 text-surface-400" />
                          <span>Posted {new Date(selectedJob.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>

                      {/* Action Bar */}
                      <div className="flex items-center gap-3 mt-5 pt-4 border-t border-surface-100">
                        {isOwnerOfSelected ? (
                          <>
                            <Button
                              variant="primary"
                              size="md"
                              onClick={() => setIsAtsOpen(true)}
                              leftIcon={<Users className="w-4 h-4" />}
                            >
                              View ATS Pipeline ({selectedJob.application_count})
                            </Button>
                            <Button
                              variant="outline"
                              size="md"
                              onClick={() => handleToggleJobStatus(selectedJob)}
                            >
                              {selectedJob.status === 'OPEN' ? 'Close Requisition' : 'Re-open Requisition'}
                            </Button>
                          </>
                        ) : selectedJob.has_viewer_applied ? (
                          <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-50 border border-brand-200 text-brand-800 text-xs font-bold">
                            <CheckCircle2 className="w-4 h-4 text-brand-600" />
                            <span>
                              Application Submitted (Status:{' '}
                              {selectedJob.viewer_application_status || 'APPLIED'})
                            </span>
                          </div>
                        ) : (
                          <Button
                            variant="primary"
                            size="md"
                            onClick={() => setIsApplyOpen(true)}
                            disabled={selectedJob.status === 'CLOSED'}
                            leftIcon={<Send className="w-4 h-4" />}
                          >
                            Easy Apply Now
                          </Button>
                        )}
                      </div>
                    </div>

                    {/* Required Skills Chips */}
                    {selectedJob.required_skills && selectedJob.required_skills.length > 0 && (
                      <div>
                        <h4 className="text-xs font-bold text-surface-900 uppercase tracking-wider mb-2">
                          Required Technical Skills
                        </h4>
                        <div className="flex flex-wrap gap-1.5">
                          {selectedJob.required_skills.map((skill) => (
                            <span
                              key={skill}
                              className="bg-surface-100 text-surface-800 font-semibold text-xs px-2.5 py-1 rounded-md border border-surface-200"
                            >
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Description Narrative */}
                    <div>
                      <h4 className="text-xs font-bold text-surface-900 uppercase tracking-wider mb-2">
                        About the Role
                      </h4>
                      <p className="text-xs text-surface-700 leading-relaxed whitespace-pre-line">
                        {selectedJob.description}
                      </p>
                    </div>

                    {/* Hiring Manager Summary */}
                    <div className="p-4 rounded-xl bg-surface-50 border border-surface-200 space-y-2">
                      <span className="text-[11px] font-bold text-surface-500 uppercase tracking-wider">
                        Posted by Hiring Manager
                      </span>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <Avatar
                            src={selectedJob.poster.avatar_url}
                            alt={selectedJob.poster.full_name}
                            size="md"
                          />
                          <div>
                            <button
                              onClick={() => onSelectUser?.(selectedJob.poster.id)}
                              className="font-bold text-xs text-surface-900 hover:text-brand-600 block text-left"
                            >
                              {selectedJob.poster.full_name}
                            </button>
                            <span className="text-[11px] text-surface-500 line-clamp-1">
                              {selectedJob.poster.headline}
                            </span>
                          </div>
                        </div>

                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => onSelectUser?.(selectedJob.poster.id)}
                        >
                          View Profile
                        </Button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-20 text-surface-400 text-xs">
                    Select a job from the list to preview details and apply.
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* VIEW: MY APPLICATIONS */}
      {activeTab === 'my-applications' && (
        <div className="space-y-4">
          {/* 1. Loading Skeleton */}
          {loadingApps && (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="bg-white rounded-xl border border-surface-200 p-5 space-y-3">
                  <Skeleton width="40%" height={18} />
                  <Skeleton width="25%" height={14} />
                  <Skeleton width="60%" height={12} />
                </div>
              ))}
            </div>
          )}

          {/* 2. Error State */}
          {!loadingApps && appsError && (
            <div className="bg-white rounded-xl border border-danger-200 p-8 text-center space-y-3 shadow-elevation-1">
              <AlertTriangle className="w-10 h-10 text-danger-600 mx-auto" />
              <h3 className="text-base font-bold text-surface-900">Failed to Retrieve Applications</h3>
              <p className="text-xs text-surface-600 max-w-sm mx-auto">{appsError}</p>
              <Button
                variant="primary"
                size="sm"
                onClick={fetchMyApplications}
                leftIcon={<RefreshCw className="w-4 h-4" />}
              >
                Retry
              </Button>
            </div>
          )}

          {/* 3. Empty State */}
          {!loadingApps && !appsError && myApplications.length === 0 && (
            <div className="bg-white rounded-xl border border-surface-200 p-12 text-center space-y-3 shadow-elevation-1">
              <FileCheck className="w-12 h-12 text-surface-400 mx-auto" />
              <h3 className="text-base font-bold text-surface-900">No Applications Submitted Yet</h3>
              <p className="text-xs text-surface-500 max-w-sm mx-auto">
                Explore open requisitions in engineering, cloud infrastructure, and product design, then submit your Easy Apply application.
              </p>
              <Button
                variant="primary"
                size="sm"
                onClick={() => setActiveTab('browse')}
              >
                Browse Open Roles
              </Button>
            </div>
          )}

          {/* 4. Populated Applications List */}
          {!loadingApps && !appsError && myApplications.length > 0 && (
            <div className="space-y-3">
              {myApplications.map((app) => (
                <div
                  key={app.id}
                  className="bg-white rounded-xl border border-surface-200 p-5 shadow-elevation-1 space-y-3 hover:border-brand-300 transition-all"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div>
                      <h4 className="text-sm font-bold text-surface-900">
                        {app.job_title || 'Engineering Role'}
                      </h4>
                      <p className="text-xs font-semibold text-brand-700">
                        {app.company_name || 'ProNet Partner'}
                      </p>
                    </div>

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
                      size="md"
                    >
                      {app.status}
                    </Badge>
                  </div>

                  {app.cover_note && (
                    <div className="p-3 bg-surface-50 rounded-lg text-xs text-surface-700 italic border border-surface-100">
                      &ldquo;{app.cover_note}&rdquo;
                    </div>
                  )}

                  <div className="flex items-center justify-between pt-2 border-t border-surface-100 text-xs text-surface-500">
                    <span className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5" />
                      Submitted on {new Date(app.created_at).toLocaleDateString()}
                    </span>

                    {app.resume_url && (
                      <a
                        href={app.resume_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-brand-600 hover:underline font-semibold"
                      >
                        <span>View Resume</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Modals */}
      <CreateJobModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onSuccess={handleJobCreated}
      />

      {selectedJob && (
        <>
          <EasyApplyModal
            job={selectedJob}
            isOpen={isApplyOpen}
            onClose={() => setIsApplyOpen(false)}
            onSuccess={handleApplicationSuccess}
          />

          <RecruiterPipelineModal
            jobId={selectedJob.id}
            jobTitle={selectedJob.title}
            isOpen={isAtsOpen}
            onClose={() => setIsAtsOpen(false)}
            onSelectApplicant={onSelectUser}
          />
        </>
      )}
    </div>
  );
};
