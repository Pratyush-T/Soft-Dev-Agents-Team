import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { SkillDTO } from '../../types/api';
import { Plus, X, Search } from 'lucide-react';

export interface SkillsCardProps {
  skills: SkillDTO[];
  isOwnProfile: boolean;
  onAddSkill: (name: string) => void;
  onRemoveSkill: (id: string) => void;
}

export const SkillsCard: React.FC<SkillsCardProps> = ({
  skills,
  isOwnProfile,
  onAddSkill,
  onRemoveSkill,
}) => {
  const [isAdding, setIsAdding] = useState(false);
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<SkillDTO[]>([]);

  useEffect(() => {
    if (query.trim().length > 0) {
      api.users
        .getSkills(query)
        .then((res) => {
          setSuggestions(res);
        })
        .catch(() => {
          setSuggestions([]);
        });
    } else {
      setSuggestions([]);
    }
  }, [query]);

  const handleCommitSkill = (name: string) => {
    if (!name.trim()) return;
    onAddSkill(name.trim());
    setQuery('');
    setSuggestions([]);
    setIsAdding(false);
  };

  return (
    <div className="bg-white rounded-xl border border-surface-200 shadow-elevation-1 p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-surface-900">Skills & Endorsements</h3>
          <p className="text-xs text-surface-500">Core technologies, frameworks, and architecture disciplines</p>
        </div>
        {isOwnProfile && (
          <button
            onClick={() => setIsAdding(!isAdding)}
            className="flex items-center gap-1 text-xs text-brand-600 font-semibold hover:bg-brand-50 px-2.5 py-1.5 rounded-lg transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            Add Skill
          </button>
        )}
      </div>

      {/* Autocomplete Input */}
      {isAdding && (
        <div className="p-3 bg-surface-50 rounded-lg border border-surface-200 space-y-2">
          <div className="relative">
            <Search className="w-4 h-4 text-surface-400 absolute left-2.5 top-2.5 pointer-events-none" />
            <input
              type="text"
              placeholder="Search or type a new skill (e.g. Distributed Systems, eBPF)..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleCommitSkill(query);
                }
              }}
              className="w-full text-xs rounded-md border border-surface-200 pl-8 pr-16 py-2 bg-white focus:outline-none focus:border-brand-600"
              autoFocus
            />
            <button
              onClick={() => handleCommitSkill(query)}
              disabled={!query.trim()}
              className="absolute right-1.5 top-1.5 text-xs bg-brand-600 hover:bg-brand-700 text-white font-medium px-2 py-1 rounded disabled:opacity-40"
            >
              Add
            </button>
          </div>

          {suggestions.length > 0 && (
            <div className="flex flex-wrap gap-1.5 pt-1">
              {suggestions.map((s) => (
                <button
                  key={s.id}
                  onClick={() => handleCommitSkill(s.name)}
                  className="text-xs bg-white hover:bg-brand-50 hover:text-brand-700 border border-surface-200 px-2.5 py-1 rounded-full text-surface-700 transition-colors"
                >
                  + {s.name}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Skills Chips */}
      {skills.length === 0 ? (
        <p className="text-xs text-surface-400 italic">No skills added yet.</p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {skills.map((skill) => (
            <span
              key={skill.id}
              className="inline-flex items-center gap-1.5 px-3 py-1 bg-surface-100 text-surface-800 border border-surface-200 rounded-full text-xs font-medium"
            >
              {skill.name}
              {isOwnProfile && (
                <button
                  onClick={() => onRemoveSkill(skill.id)}
                  className="text-surface-400 hover:text-danger-600 p-0.5 rounded-full hover:bg-surface-200 transition-colors"
                  title={`Remove ${skill.name}`}
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};
