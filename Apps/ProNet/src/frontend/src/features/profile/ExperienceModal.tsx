import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { ExperienceDTO } from '../../types/api';
import { useToastStore } from '../../stores/toastStore';
import { Modal } from '../../components/ui/Modal';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';

export interface ExperienceModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialData?: ExperienceDTO | null;
  onSuccess: () => void;
}

export const ExperienceModal: React.FC<ExperienceModalProps> = ({
  isOpen,
  onClose,
  initialData,
  onSuccess,
}) => {
  const { addToast } = useToastStore();

  const [company, setCompany] = useState('');
  const [title, setTitle] = useState('');
  const [location, setLocation] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [isCurrent, setIsCurrent] = useState(false);
  const [description, setDescription] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (initialData) {
      setCompany(initialData.company);
      setTitle(initialData.title);
      setLocation(initialData.location || '');
      setStartDate(initialData.start_date);
      setEndDate(initialData.end_date || '');
      setIsCurrent(initialData.is_current);
      setDescription(initialData.description || '');
    } else {
      setCompany('');
      setTitle('');
      setLocation('');
      setStartDate('');
      setEndDate('');
      setIsCurrent(false);
      setDescription('');
    }
  }, [initialData, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!isCurrent && endDate && endDate < startDate) {
      addToast({
        type: 'error',
        title: 'Validation Error',
        message: 'End date cannot precede the start date.',
      });
      return;
    }

    setSaving(true);
    try {
      const payload = {
        company: company.trim(),
        title: title.trim(),
        location: location.trim() || null,
        start_date: startDate,
        end_date: isCurrent ? null : endDate || null,
        is_current: isCurrent,
        description: description.trim() || null,
      };

      if (initialData) {
        await api.users.updateExperience(initialData.id, payload);
        addToast({
          type: 'success',
          title: 'Experience Updated',
          message: `${title} at ${company} was updated.`,
        });
      } else {
        await api.users.addExperience(payload);
        addToast({
          type: 'success',
          title: 'Experience Added',
          message: `${title} at ${company} was added.`,
        });
      }

      onSuccess();
      onClose();
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Save Failed',
        message: err.message || 'Could not save work experience.',
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={initialData ? 'Edit Work Experience' : 'Add Work Experience'}
      size="md"
      footer={
        <>
          <Button variant="secondary" size="sm" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button variant="primary" size="sm" onClick={handleSubmit} isLoading={saving}>
            {initialData ? 'Save Changes' : 'Add Position'}
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g. Senior Distributed Systems Engineer"
          required
        />

        <Input
          label="Company Name"
          value={company}
          onChange={(e) => setCompany(e.target.value)}
          placeholder="e.g. Anthropic, Datadog, Stripe"
          required
        />

        <Input
          label="Location"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          placeholder="e.g. San Francisco, CA (or Remote)"
        />

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Start Date"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            required
          />

          {!isCurrent && (
            <Input
              label="End Date"
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          )}
        </div>

        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="isCurrent"
            checked={isCurrent}
            onChange={(e) => setIsCurrent(e.target.checked)}
            className="rounded border-surface-300 text-brand-600 focus:ring-brand-500 w-4 h-4"
          />
          <label htmlFor="isCurrent" className="text-xs font-medium text-surface-700">
            I currently work in this role
          </label>
        </div>

        <div>
          <label className="block text-sm font-medium text-surface-700 mb-1">
            Description & Key Architectural Accomplishments
          </label>
          <textarea
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Key responsibilities, technical stacks used, architecture metrics achieved..."
            className="w-full text-sm rounded-md border border-surface-200 bg-white p-3 focus:outline-none focus:border-brand-600 focus:ring-1 focus:ring-brand-600 text-surface-900"
          />
        </div>
      </form>
    </Modal>
  );
};
