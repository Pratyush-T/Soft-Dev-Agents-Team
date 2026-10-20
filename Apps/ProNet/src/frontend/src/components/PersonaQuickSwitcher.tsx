import React, { useState, useEffect, useRef } from 'react';
import { useAuthStore } from '../stores/authStore';
import { api } from '../services/api';
import { PersonaDTO } from '../types/api';
import { Avatar } from './ui/Avatar';
import { Check, ChevronDown, Search, Sparkles } from 'lucide-react';

// Static fallback metadata for the 10 deterministic seed personas
const FALLBACK_PERSONAS: (PersonaDTO & { roleCategory: string })[] = [
  {
    id: 'usr_elena_rostova',
    email: 'elena.rostova@pronet.local',
    full_name: 'Elena Rostova',
    headline: 'Staff AI Systems Engineer | Distributed LLM Training & Kernel Optimization',
    location: 'San Francisco, CA',
    avatar_url: null,
    roleCategory: 'Engineering Staff',
  },
  {
    id: 'usr_alex_chen',
    email: 'alex.chen@pronet.local',
    full_name: 'Alex Chen',
    headline: 'Principal Cloud Infrastructure Architect | Kubernetes & High-Resilience Systems',
    location: 'Seattle, WA',
    avatar_url: null,
    roleCategory: 'Cloud & Infra',
  },
  {
    id: 'usr_marcus_vance',
    email: 'marcus.vance@pronet.local',
    full_name: 'Marcus Vance',
    headline: 'VP of Engineering & Platform Scalability | Building High-Velocity Orgs',
    location: 'Austin, TX',
    avatar_url: null,
    roleCategory: 'Executive Leadership',
  },
  {
    id: 'usr_priya_sharma',
    email: 'priya.sharma@pronet.local',
    full_name: 'Priya Sharma',
    headline: 'Lead Full-Stack Engineer | React 18 & Async Python Architecture',
    location: 'New York, NY',
    avatar_url: null,
    roleCategory: 'Frontend & Full-Stack',
  },
  {
    id: 'usr_devon_taylor',
    email: 'devon.taylor@pronet.local',
    full_name: 'Devon Taylor',
    headline: 'Head of Product Design | Design Systems & Cognitive Ergonomics',
    location: 'San Francisco, CA',
    avatar_url: null,
    roleCategory: 'Design & UX',
  },
  {
    id: 'usr_sarah_jenkins',
    email: 'sarah.jenkins@pronet.local',
    full_name: 'Sarah Jenkins',
    headline: 'Principal Technical Talent Partner | Executive Tech Recruiter',
    location: 'Boston, MA',
    avatar_url: null,
    roleCategory: 'Technical Talent',
  },
  {
    id: 'usr_liam_patel',
    email: 'liam.patel@pronet.local',
    full_name: 'Liam Patel',
    headline: 'Senior Site Reliability Engineer | eBPF & Kernel Telemetry',
    location: 'Denver, CO',
    avatar_url: null,
    roleCategory: 'SRE & Systems',
  },
  {
    id: 'usr_zack_kowalski',
    email: 'zack.kowalski@pronet.local',
    full_name: 'Zack Kowalski',
    headline: 'Staff Data Platform Engineer | Apache Kafka & Flink Streaming',
    location: 'Chicago, IL',
    avatar_url: null,
    roleCategory: 'Data Platform',
  },
  {
    id: 'usr_aisha_diop',
    email: 'aisha.diop@pronet.local',
    full_name: 'Aisha Diop',
    headline: 'Director of Product Management | Developer Platforms & Enterprise APIs',
    location: 'New York, NY',
    avatar_url: null,
    roleCategory: 'Product Leadership',
  },
  {
    id: 'usr_jordan_mendez',
    email: 'jordan.mendez@pronet.local',
    full_name: 'Jordan Mendez',
    headline: 'Cybersecurity & Identity Architect | Zero-Trust & Cryptographic Infrastructure',
    location: 'Washington, DC',
    avatar_url: null,
    roleCategory: 'Security & Identity',
  },
];

export const PersonaQuickSwitcher: React.FC = () => {
  const { currentUser, activePersonaId, quickSwitchPersona } = useAuthStore();
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [personas, setPersonas] = useState<(PersonaDTO & { roleCategory?: string })[]>(FALLBACK_PERSONAS);
  const [isSwitching, setIsSwitching] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Attempt to load personas from backend
    api.auth
      .getPersonas()
      .then((data) => {
        if (data && data.length > 0) {
          const merged = data.map((p) => {
            const fallback = FALLBACK_PERSONAS.find((f) => f.id === p.id);
            return {
              ...p,
              roleCategory: fallback?.roleCategory || 'Professional',
            };
          });
          setPersonas(merged);
        }
      })
      .catch((e) => {
        console.warn('[PersonaSwitcher] Using fallback persona registry:', e);
      });
  }, []);

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelectPersona = async (personaId: string) => {
    if (personaId === activePersonaId) {
      setIsOpen(false);
      return;
    }
    setIsSwitching(true);
    try {
      await quickSwitchPersona(personaId);
      setIsOpen(false);
    } catch (e) {
      console.error('[PersonaSwitcher] Quick switch failed:', e);
    } finally {
      setIsSwitching(false);
    }
  };

  const filteredPersonas = personas.filter(
    (p) =>
      p.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.headline.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (p.roleCategory && p.roleCategory.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const activePersona = personas.find((p) => p.id === activePersonaId) || currentUser;

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 p-1.5 rounded-lg border border-surface-200 hover:border-brand-300 hover:bg-surface-50 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600"
        title="Switch active user persona"
        aria-label="Active Developer Persona Quick Switcher"
      >
        <Avatar
          src={currentUser?.avatar_url || activePersona?.avatar_url || null}
          alt={currentUser?.full_name || activePersona?.full_name || 'User'}
          size="sm"
          isOnline={true}
        />
        <div className="text-left hidden lg:block max-w-[150px]">
          <div className="text-xs font-bold text-surface-900 truncate">
            {currentUser?.full_name || activePersona?.full_name || 'Select Persona'}
          </div>
          <div className="text-[10px] text-surface-500 truncate">
            {currentUser?.headline?.split('|')[0].trim() || 'Click to switch'}
          </div>
        </div>
        <ChevronDown className="w-4 h-4 text-surface-500 shrink-0" />
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 max-w-[calc(100vw-2rem)] bg-white border border-surface-200 rounded-xl shadow-elevation-3 z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-100">
          {/* Header */}
          <div className="p-3 bg-surface-50 border-b border-surface-200">
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-1.5 text-xs font-bold text-surface-900">
                <Sparkles className="w-3.5 h-3.5 text-brand-600" />
                Active Developer Persona
              </div>
              <span className="text-[10px] font-semibold bg-brand-50 text-brand-700 border border-brand-200 px-1.5 py-0.5 rounded">
                SQLite WAL
              </span>
            </div>
            <p className="text-[11px] text-surface-500 leading-tight">
              Instant 1-click identity, JWT credentials, and social graph switching across all 10 pre-seeded profiles.
            </p>
          </div>

          {/* Filter Input */}
          <div className="p-2 border-b border-surface-200">
            <div className="relative">
              <Search className="w-4 h-4 text-surface-400 absolute left-2.5 top-2.5" />
              <input
                type="text"
                placeholder="Search persona by name or role..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 text-xs rounded-md border border-surface-200 focus:outline-none focus:border-brand-600 focus:ring-1 focus:ring-brand-600 bg-surface-50"
                autoFocus
              />
            </div>
          </div>

          {/* Persona List */}
          <div className="max-h-80 overflow-y-auto divide-y divide-surface-100">
            {filteredPersonas.map((persona) => {
              const isActive = persona.id === activePersonaId;
              return (
                <button
                  key={persona.id}
                  onClick={() => handleSelectPersona(persona.id)}
                  disabled={isSwitching}
                  className={`w-full text-left p-3 flex items-start gap-3 transition-colors ${
                    isActive ? 'bg-brand-50/70 hover:bg-brand-50' : 'hover:bg-surface-50'
                  }`}
                >
                  <Avatar src={persona.avatar_url} alt={persona.full_name} size="md" isOnline={isActive} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-surface-900 truncate">
                        {persona.full_name}
                      </span>
                      {isActive && (
                        <span className="flex items-center gap-1 text-[10px] font-bold text-brand-700 bg-brand-100 px-1.5 py-0.5 rounded">
                          <Check className="w-3 h-3" />
                          ACTIVE
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-surface-600 line-clamp-1 mt-0.5">
                      {persona.headline}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[10px] font-medium bg-surface-100 text-surface-700 px-1.5 py-0.2 rounded border border-surface-200">
                        {persona.roleCategory || 'Engineer'}
                      </span>
                      <span className="text-[10px] text-surface-400">{persona.location}</span>
                    </div>
                  </div>
                </button>
              );
            })}

            {filteredPersonas.length === 0 && (
              <div className="p-6 text-center text-xs text-surface-500">
                No persona found matching &quot;{searchQuery}&quot;
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-2.5 bg-surface-50 border-t border-surface-200 text-center">
            <span className="text-[10px] text-surface-400">
              Deterministic Seed Fixture v1.0 • 10 Users • 15 Edges • 12 Posts • 8 Jobs
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
