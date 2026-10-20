import React from 'react';
import { EducationDTO } from '../../types/api';
import { GraduationCap, Plus, Edit2, Trash2, Calendar } from 'lucide-react';

export interface EducationTimelineProps {
  educations: EducationDTO[];
  isOwnProfile: boolean;
  onAdd: () => void;
  onEdit: (edu: EducationDTO) => void;
  onDelete: (id: string) => void;
}

export const EducationTimeline: React.FC<EducationTimelineProps> = ({
  educations,
  isOwnProfile,
  onAdd,
  onEdit,
  onDelete,
}) => {
  return (
    <div className="bg-white rounded-xl border border-surface-200 shadow-elevation-1 p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-surface-900">Education</h3>
          <p className="text-xs text-surface-500">Academic degrees, institutions, and fields of study</p>
        </div>
        {isOwnProfile && (
          <button
            onClick={onAdd}
            className="flex items-center gap-1 text-xs text-brand-600 font-semibold hover:bg-brand-50 px-2.5 py-1.5 rounded-lg transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            Add Education
          </button>
        )}
      </div>

      {educations.length === 0 ? (
        <div className="py-6 text-center border border-dashed border-surface-200 rounded-lg">
          <GraduationCap className="w-8 h-8 text-surface-300 mx-auto mb-2" />
          <p className="text-xs text-surface-500">No education listed yet.</p>
          {isOwnProfile && (
            <button
              onClick={onAdd}
              className="mt-2 text-xs text-brand-600 font-semibold hover:underline"
            >
              + Add Education
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {educations.map((edu) => (
            <div key={edu.id} className="flex items-start gap-3.5 group">
              <div className="w-10 h-10 rounded-lg bg-surface-100 border border-surface-200 flex items-center justify-center text-surface-600 shrink-0 mt-0.5">
                <GraduationCap className="w-5 h-5 text-surface-500" />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h4 className="text-sm font-bold text-surface-900">{edu.institution}</h4>
                    <span className="text-xs font-medium text-surface-700">
                      {edu.degree}
                      {edu.field_of_study ? ` in ${edu.field_of_study}` : ''}
                    </span>
                  </div>

                  {isOwnProfile && (
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => onEdit(edu)}
                        className="p-1 text-surface-400 hover:text-brand-600 rounded transition-colors"
                        title="Edit education"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => onDelete(edu.id)}
                        className="p-1 text-surface-400 hover:text-danger-600 rounded transition-colors"
                        title="Delete education"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-1 text-xs text-surface-500 mt-1">
                  <Calendar className="w-3 h-3 text-surface-400" />
                  <span>
                    {edu.start_year} – {edu.end_year ?? 'Present'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
