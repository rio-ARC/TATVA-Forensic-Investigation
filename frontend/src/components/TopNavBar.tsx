import { useNavigate, useLocation } from 'react-router-dom'

interface TopNavBarProps {
  avatarSrc: string
}

const NAV_LINKS = [
  { label: 'Dashboard', path: '/case/new' },
]

export default function TopNavBar({ avatarSrc }: TopNavBarProps) {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <header
      className="bg-[#131314]/80 backdrop-blur-xl fixed top-0 left-0 w-full z-50 flex justify-between items-center border-b border-[#3f4852]/30 h-16"
      style={{ padding: '0 32px' }}
    >
      {/* Left: Logo + Nav */}
      <div className="flex items-center gap-8">
        <span
          className="text-headline-xl font-black tracking-widest cursor-pointer"
          style={{ color: '#feb700' }}
          onClick={() => navigate('/')}
        >
          TATVA
        </span>
        <nav className="hidden md:flex gap-6">
          {NAV_LINKS.map((link) => {
            const isActive = location.pathname === link.path
            return (
              <a
                key={link.path}
                href="#"
                onClick={(e) => { e.preventDefault(); navigate(link.path) }}
                className={`font-medium transition-colors duration-200 ${isActive
                  ? 'text-[#ffdb9d] font-bold border-b-2 border-[#feb700] pb-1'
                  : 'text-[#bec7d4] hover:text-[#ffdb9d]'
                }`}
                style={{ fontFamily: 'Geist, sans-serif', fontSize: '16px' }}
              >
                {link.label}
              </a>
            )
          })}
        </nav>
      </div>

      {/* Right: Search + Icons + Avatar */}
      <div className="flex items-center gap-4">
        {/* Search */}
        <div className="relative hidden lg:block">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[#bec7d4]" style={{ fontSize: '18px' }}>
            search
          </span>
          <input
            type="text"
            placeholder="Search case repository..."
            className="bg-[#1c1b1c] border border-[#3f4852]/30 rounded-lg pl-10 pr-4 py-1.5 text-[#e5e2e3] focus:ring-1 focus:ring-[#feb700] focus:border-[#feb700] outline-none w-64 transition-all"
            style={{ fontFamily: 'Geist', fontSize: '14px' }}
          />
        </div>

        {/* Notification */}
        <div className="relative group">
          <button className="material-symbols-outlined text-[#bec7d4] hover:text-[#ffdb9d] transition-colors">
            notifications
          </button>
          <div className="absolute top-0 right-0 w-2 h-2 bg-[#ffb4ab] rounded-full border-2 border-[#131314]" />
        </div>

        {/* Settings */}
        <button className="material-symbols-outlined text-[#bec7d4] hover:text-[#ffdb9d] transition-colors">
          settings
        </button>

        {/* Profile */}
        <div className="flex items-center gap-2 pl-4 border-l border-[#3f4852]/30">
          <img
            src={avatarSrc}
            alt="Investigator Profile"
            className="w-8 h-8 rounded-full border border-[#feb700]/30 object-cover"
          />
          <span className="text-technical-sm text-[#bec7d4] hidden lg:block">
            ID-9422 // AGENT
          </span>
        </div>
      </div>
    </header>
  )
}
