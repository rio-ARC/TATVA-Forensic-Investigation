import { useNavigate, useLocation } from 'react-router-dom'

interface NavItem {
  icon: string
  label: string
  path: string
}

const NAV_ITEMS: NavItem[] = [
  { icon: 'folder_open', label: 'Evidence Vault', path: '/evidence' },
  { icon: 'hub', label: 'Entity Graph', path: '/investigation' },
  { icon: 'description', label: 'Case Files', path: '/case/new' },
  { icon: 'smart_card_reader', label: 'Digital Forensics', path: '/forensics' },
  { icon: 'history', label: 'Timeline', path: '/reconstruction' },
]

export default function SideNavBar() {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <aside
      className="flex flex-col h-full bg-[#1c1b1c]/90 backdrop-blur-md border-r border-[#3f4852]/20 w-64"
      style={{ padding: '24px 0' }}
    >
      {/* Header */}
      <div className="px-6 mb-8">
        <div className="flex items-center gap-3 mb-1">
          <span className="material-symbols-outlined text-[#e5e2e3]" style={{ fontVariationSettings: "'FILL' 1" }}>
            shield
          </span>
          <div>
            <div className="text-headline-md text-[#e5e2e3]">Unit 01</div>
            <div className="text-technical-sm text-[#bec7d4] uppercase tracking-widest">Forensic Division</div>
          </div>
        </div>
        <button
          onClick={() => navigate('/case/new')}
          className="w-full mt-6 border border-[#feb700]/30 py-3 flex items-center justify-center gap-2 transition-all duration-300 hover:bg-[#feb700]/10"
          style={{ color: '#ffdb9d', background: 'rgba(254,183,0,0.05)' }}
        >
          <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>add</span>
          <span className="text-technical-md uppercase tracking-wider">New Investigation</span>
        </button>
      </div>

      {/* Search */}
      <div className="px-6 py-2 mb-2">
        <div className="relative">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[#bec7d4]" style={{ fontSize: '18px' }}>
            search
          </span>
          <input
            type="text"
            placeholder="SEARCH ENTITIES..."
            className="w-full bg-[#353436]/50 border-none outline-none py-2 pl-10 text-[#e5e2e3] placeholder:text-[#bec7d4]/50 focus:ring-1 focus:ring-[#feb700]/50"
            style={{ fontFamily: 'JetBrains Mono', fontSize: '12px' }}
          />
        </div>
      </div>

      {/* Nav Items */}
      <div className="flex-1 overflow-y-auto space-y-1">
        {NAV_ITEMS.map((item) => {
          const isActive = location.pathname === item.path
          return (
            <a
              key={item.path}
              href="#"
              onClick={(e) => { e.preventDefault(); navigate(item.path) }}
              className={`flex items-center gap-3 px-6 py-3 transition-all duration-300 ${isActive
                ? 'bg-[#feb700]/10 text-[#ffdb9d] border-r-4 border-[#feb700]'
                : 'text-[#bec7d4] hover:bg-[#353436]/40 hover:text-[#e5e2e3]'
              }`}
            >
              <span className="material-symbols-outlined">{item.icon}</span>
              <span className="text-technical-md uppercase tracking-wider">{item.label}</span>
              {isActive && item.path === '/investigation' && (
                <span className="ml-auto bg-[#feb700] text-[#412d00] px-1.5 py-0.5 rounded-sm text-[10px] font-bold">
                  LIVE
                </span>
              )}
            </a>
          )
        })}
      </div>

      {/* Footer */}
      <div className="mt-auto pt-4 border-t border-[#3f4852]/20">
        <a href="#" className="flex items-center gap-3 text-[#bec7d4] px-6 py-2 hover:text-[#e5e2e3] transition-colors">
          <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>help</span>
          <span className="text-technical-sm uppercase tracking-widest">Help Center</span>
        </a>
        <a href="#" className="flex items-center gap-3 text-[#bec7d4] px-6 py-2 hover:text-[#e5e2e3] transition-colors">
          <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>analytics</span>
          <span className="text-technical-sm uppercase tracking-widest">System Status</span>
        </a>
      </div>
    </aside>
  )
}
