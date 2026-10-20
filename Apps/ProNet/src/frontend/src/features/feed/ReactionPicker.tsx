import React from 'react';
import { ReactionType } from '../../types/api';
import { ThumbsUp, PartyPopper, Lightbulb } from 'lucide-react';

export interface ReactionPickerProps {
  onSelect: (type: ReactionType) => void;
  activeReaction: ReactionType | null;
}

export const ReactionPicker: React.FC<ReactionPickerProps> = ({ onSelect, activeReaction }) => {
  return (
    <div
      className="flex items-center gap-1.5 p-1.5 bg-white border border-surface-200 rounded-full shadow-elevation-2 animate-in fade-in zoom-in-95 duration-100"
      role="toolbar"
      aria-label="Reactions picker"
    >
      <button
        type="button"
        onClick={() => onSelect('LIKE')}
        className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold transition-transform hover:scale-110 ${
          activeReaction === 'LIKE' ? 'bg-brand-50 text-brand-600' : 'hover:bg-surface-100 text-surface-700'
        }`}
        title="Like"
      >
        <ThumbsUp className="w-4 h-4 text-brand-600 fill-brand-600/20" />
        <span className="hidden sm:inline">Like</span>
      </button>

      <button
        type="button"
        onClick={() => onSelect('CELEBRATE')}
        className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold transition-transform hover:scale-110 ${
          activeReaction === 'CELEBRATE' ? 'bg-success-50 text-success-600' : 'hover:bg-surface-100 text-surface-700'
        }`}
        title="Celebrate"
      >
        <PartyPopper className="w-4 h-4 text-success-600" />
        <span className="hidden sm:inline">Celebrate</span>
      </button>

      <button
        type="button"
        onClick={() => onSelect('INSIGHTFUL')}
        className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold transition-transform hover:scale-110 ${
          activeReaction === 'INSIGHTFUL' ? 'bg-warning-50 text-warning-600' : 'hover:bg-surface-100 text-surface-700'
        }`}
        title="Insightful"
      >
        <Lightbulb className="w-4 h-4 text-warning-600 fill-warning-600/20" />
        <span className="hidden sm:inline">Insightful</span>
      </button>
    </div>
  );
};
