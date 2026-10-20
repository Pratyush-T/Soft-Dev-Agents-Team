import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { EducationDTO } from '../../types/api';
import { useToastStore } from '../../stores/toastStore';
import { Modal } from '../../components/ui/Modal';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';

export interface EducationModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialData?: EducationDTO | null;
  onSuccess: () => void;
}

export const EducationModal: React.FC<EducationModalProps> = ({
  isOpen,
  onClose,
  initialData,
  onSuccess,
}) => {
  const { addToast } = useToastStore();

  const [institution, setInstitution] = useState('');
  const [degree, setDegree] = useState('');
  const [fieldOfStudy, setFieldOfStudy] = useState('');
  const [startYear, setStartYear] = useState<number>(new Date().getFullYear() - 4);
  const [endYear, setEndYear] = useState<number | string>(new Date().getFullYear());
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (initialData) {
      setInstitution(initialData.institution);
      setDegree(initialData.degree);
      setFieldOfStudy(initialData.field_of_study || '');
      setStartYear(initialData.start_year);
      setEndYear(initialData.end_year ?? '');
    } else {
      setInstitution('');
      setDegree('');
      setFieldOfStudy('');
      setStartYear(new Date().getFullYear() - 4);
      setEndYear(new Date().getFullYear());
    }
  }, [initialData, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    setSaving(true);
    try {
      const payload = {
        institution: institution.trim(),
        degree: degree.trim(),
        field_of_study: fieldOfStudy.trim() || null,
        start_year: Number(startYear),
        end_year: endYear ? Number(endYear) : null,
      };

      if (initialData) {
        await api.users.updateEducation(initialData.id, payload);
        addToast({
          type: 'success',
          title: 'Education Updated',
          message: `${institution} record updated.`,
        });
      } else {
        await api.users.addEducation(payload);
        addToast({
          type: 'success',
          title: 'Education Added',
          message: `${institution} record added.`,
        });
      }

      onSuccess();
      onClose();
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Save Failed',
        message: err.message || 'Could not save education record.',
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={initialData ? 'Edit Education' : 'Add Education'}
      size="md"
      footer={
        <>
          <Button variant="secondary" size="sm" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button variant="primary" size="sm" onClick={handleSubmit} isLoading={saving}>
            {initialData ? 'Save Changes' : 'Add Education'}
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="School / University"
          value={institution}
          onChange={(e) => setInstitution(e.target.value)}
          placeholder="e.g. Stanford University, MIT, UC Berkeley"
          required
        />

        <Input
          label="Degree"
          value={degree}
          onChange={(e) => setDegree(e.target.value)}
          placeholder="e.g. Bachelor of Science, Master of Science"
          required
        />

        <Input
          label="Field of Study"
          value={fieldOfStudy}
          onChange={(e) => setFieldOfStudy(e.target.value)}
          placeholder="e.g. Computer Science, Electrical Engineering"
        />

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Start Year"
            type="number"
            min={1950}
            max={2100}
            value={startYear}
            onChange={(e) => setStartYear(Number(e.target.value))}
            required
          />

          <Input
            label="End Year (or Expected)"
            type="number"
            min={1950}
            max={2100}
            value={endYear}
            onChange={(e) => setEndYear(e.target.value)}
          />
        </div>
      </form>
    </Modal>
  );
};
