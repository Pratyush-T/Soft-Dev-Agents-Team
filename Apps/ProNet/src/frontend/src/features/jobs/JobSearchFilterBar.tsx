import React from 'react';
import { JobFilterParams, WorkplaceType } from '../../types/api';
import { Search, MapPin, Briefcase, Filter } from 'lucide-react';

export interface JobSearchFilterBarProps {
  filters: JobFilterParams;
  onChange: (filters: JobFilterParams) => void;
  onPostJobClick?: () => void;
}

export const JobSearchFilterBar: React.FC<JobSearchFilterBarProps> = ({
  filters,
  onChange,
  onPostJobClick,
}) => {
  return (
    <div className="bg-white rounded-xl border border-surface-200 shadow-elevation-1 p-3.5 space-y-3">
      <div className="flex flex-col md:flex-row gap-3">
        {/* Keyword Search */}
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-surface-400 absolute left-3 top-2.5 pointer-events-none" />
          <input
            type="text"
            placeholder="Search by title, role, or keywords..."
            value={filters.keyword || ''}
            onChange={(e) => onChange({ ...filters, keyword: e.target.value || undefined })}
            className="w-full text-xs rounded-lg border border-surface-200 bg-surface-50 pl-9 pr-3 py-2 focus:outline-none focus:border-brand-600 focus:bg-white"
          />
        </div>

        {/* Location Filter */}
        <div className="relative w-full md:w-56">
          <MapPin className="w-4 h-4 text-surface-400 absolute left-3 top-2.5 pointer-events-none" />
          <input
            type="text"
            placeholder="City, State, or Country"
            value={filters.location || ''}
            onChange={(e) => onChange({ ...filters, location: e.target.value || undefined })}
            className="w-full text-xs rounded-lg border border-surface-200 bg-surface-50 pl-9 pr-3 py-2 focus:outline-none focus:border-brand-600 focus:bg-white"
          />
        </div>

        {/* Workplace Type Dropdown */}
        <div className="relative w-full md:w-44">
          <Briefcase className="w-4 h-4 text-surface-400 absolute left-3 top-2.5 pointer-events-none" />
          <select
            value={filters.workplace_type || ''}
            onChange={(e) =>
              onChange({
                ...filters,
                workplace_type: (e.target.value as WorkplaceType) || undefined,
              })
            }
            className="w-full text-xs rounded-lg border border-surface-200 bg-surface-50 pl-9 pr-7 py-2 focus:outline-none focus:border-brand-600 focus:bg-white text-surface-700 appearance-none cursor-pointer"
          >
            <option value="">All Workplace Types</option>
            <option value="REMOTE">Remote</option>
            <option value="HYBRID">Hybrid</option>
            <option value="ON_SITE">On-site</option>
          </select>
        </div>

        {/* Post Job Button */}
        {onPostJobClick && (
          <button
            onClick={onPostJobClick}
            className="bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold px-4 py-2 rounded-lg shrink-0 transition-colors shadow-sm"
          >
            + Post a Job
          </button>
        )}
      </div>

      {/* Active filters pill list */}
      {(filters.keyword || filters.location || filters.workplace_type || filters.skill) && (
        <div className="flex items-center gap-2 pt-2 border-t border-surface-100 flex-wrap text-xs">
          <span className="flex items-center gap-1 text-surface-500 font-medium">
            <Filter className="w-3.5 h-3.5" /> Filtered by:
          </span>
          {filters.keyword && (
            <span className="bg-brand-50 text-brand-700 px-2 py-0.5 rounded-full border border-brand-200">
              Keyword: {filters.keyword}
            </span>
          )}
          {filters.location && (
            <span className="bg-brand-50 text-brand-700 px-2 py-0.5 rounded-full border border-brand-200">
              Location: {filters.location}
            </span>
          )}
          {filters.workplace_type && (
            <span className="bg-brand-50 text-brand-700 px-2 py-0.5 rounded-full border border-brand-200">
              Mode: {filters.workplace_type}
            </span>
          )}
          <button
            onClick={() => onChange({})}
            className="text-brand-600 hover:underline font-semibold ml-auto"
          >
            Clear All
          </button>
        </div>
      )}
    </div>
  );
};
