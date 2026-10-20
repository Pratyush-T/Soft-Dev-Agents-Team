import React, { useState } from 'react';
import { Modal } from '../../components/ui/Modal';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { api } from '../../services/api';
import { useToastStore } from '../../stores/toastStore';
import { CreateJobDTO, JobDTO, WorkplaceType } from '../../types/api';

export interface CreateJobModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (job: JobDTO) => void;
}

export const CreateJobModal: React.FC<CreateJobModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const { addToast } = useToastStore();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState<CreateJobDTO>({
    title: '',
    company_name: '',
    workplace_type: 'REMOTE',
    location: '',
    salary_min: 120000,
    salary_max: 180000,
    description: '',
    required_skills: [],
  });
  const [skillInput, setSkillInput] = useState('');

  const handleAddSkill = (e: React.KeyboardEvent | React.MouseEvent) => {
    if ('key' in e && e.key !== 'Enter') return;
    e.preventDefault();
    const trimmed = skillInput.trim();
    if (trimmed && !formData.required_skills.includes(trimmed)) {
      setFormData({
        ...formData,
        required_skills: [...formData.required_skills, trimmed],
      });
      setSkillInput('');
    }
  };

  const handleRemoveSkill = (skillToRemove: string) => {
    setFormData({
      ...formData,
      required_skills: formData.required_skills.filter((s) => s !== skillToRemove),
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title.trim() || !formData.company_name.trim() || !formData.description.trim()) {
      addToast({
        type: 'warning',
        title: 'Missing Fields',
        message: 'Please complete all required fields.',
      });
      return;
    }

    if (formData.salary_min > formData.salary_max) {
      addToast({
        type: 'warning',
        title: 'Invalid Salary Range',
        message: 'Minimum salary cannot exceed maximum salary.',
      });
      return;
    }

    setIsSubmitting(true);
    try {
      const created = await api.jobs.createJob({
        ...formData,
        required_skills: formData.required_skills.length > 0 ? formData.required_skills : ['Engineering'],
      });
      addToast({
        type: 'success',
        title: 'Job Requisition Published',
        message: `Successfully posted ${created.title} at ${created.company_name}.`,
      });
      onSuccess(created);
      onClose();
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Posting Failed',
        message: err.message || 'Unable to create job requisition.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Post an Engineering Requisition"
      description="Create a new job posting for your team on the ProNet network."
      size="lg"
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
            disabled={!formData.title.trim() || !formData.company_name.trim()}
          >
            Publish Requisition
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4 text-xs">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input
            label="Job Title *"
            placeholder="e.g. Staff Distributed Systems Engineer"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            required
          />
          <Input
            label="Company Name *"
            placeholder="e.g. Anthropic, Datadog, Stripe"
            value={formData.company_name}
            onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
            required
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-surface-700 mb-1">
              Workplace Type *
            </label>
            <select
              value={formData.workplace_type}
              onChange={(e) =>
                setFormData({ ...formData, workplace_type: e.target.value as WorkplaceType })
              }
              className="w-full text-xs rounded-md border border-surface-200 bg-white py-2 px-3 text-surface-900 focus:outline-none focus:border-brand-600 focus:ring-1 focus:ring-brand-600 shadow-sm"
            >
              <option value="REMOTE">Remote</option>
              <option value="HYBRID">Hybrid</option>
              <option value="ON_SITE">On-Site</option>
            </select>
          </div>

          <Input
            label="Location *"
            placeholder="e.g. San Francisco, CA (or Remote US)"
            value={formData.location}
            onChange={(e) => setFormData({ ...formData, location: e.target.value })}
            required
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-surface-700 mb-1">
              Minimum Salary (USD/yr)
            </label>
            <input
              type="number"
              min={0}
              step={5000}
              value={formData.salary_min}
              onChange={(e) => setFormData({ ...formData, salary_min: Number(e.target.value) })}
              className="w-full text-xs rounded-md border border-surface-200 bg-white py-2 px-3 text-surface-900 focus:outline-none focus:border-brand-600 shadow-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-surface-700 mb-1">
              Maximum Salary (USD/yr)
            </label>
            <input
              type="number"
              min={0}
              step={5000}
              value={formData.salary_max}
              onChange={(e) => setFormData({ ...formData, salary_max: Number(e.target.value) })}
              className="w-full text-xs rounded-md border border-surface-200 bg-white py-2 px-3 text-surface-900 focus:outline-none focus:border-brand-600 shadow-sm"
            />
          </div>
        </div>

        {/* Required Skills */}
        <div>
          <label className="block text-xs font-medium text-surface-700 mb-1">
            Required Skills & Technologies
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="e.g. Python, Kubernetes, SQLite, Go"
              value={skillInput}
              onChange={(e) => setSkillInput(e.target.value)}
              onKeyDown={handleAddSkill}
              className="flex-1 text-xs rounded-md border border-surface-200 bg-white py-1.5 px-3 focus:outline-none focus:border-brand-600 shadow-sm"
            />
            <Button type="button" variant="secondary" size="sm" onClick={handleAddSkill}>
              Add
            </Button>
          </div>
          {formData.required_skills.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-2">
              {formData.required_skills.map((skill) => (
                <span
                  key={skill}
                  className="bg-brand-50 text-brand-700 border border-brand-200 px-2 py-0.5 rounded-full text-[11px] flex items-center gap-1"
                >
                  {skill}
                  <button
                    type="button"
                    onClick={() => handleRemoveSkill(skill)}
                    className="hover:text-danger-600 font-bold ml-0.5"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Description */}
        <div>
          <label className="block text-xs font-medium text-surface-700 mb-1">
            Job Description & Technical Scope *
          </label>
          <textarea
            rows={5}
            placeholder="Describe role responsibilities, tech stack, systems architecture, and candidate qualifications..."
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            className="w-full text-xs rounded-md border border-surface-200 bg-white p-3 text-surface-900 focus:outline-none focus:border-brand-600 shadow-sm leading-relaxed"
            required
          />
        </div>
      </form>
    </Modal>
  );
};
