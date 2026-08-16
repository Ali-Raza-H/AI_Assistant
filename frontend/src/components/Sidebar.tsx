type Page = 'main' | 'chat' | 'brain'

interface SidebarProps {
  page: Page
  navigate: (page: Page) => void
}

const navigation: { page: Page; index: string; label: string }[] = [
  { page: 'main', index: '01', label: 'Main' },
  { page: 'chat', index: '02', label: 'Chat' },
  { page: 'brain', index: '03', label: 'Brain' },
]

export function Sidebar({ page, navigate }: SidebarProps) {
  return (
    <aside className="sidebar">
      <button className="wordmark" onClick={() => navigate('main')} aria-label="CIEL home">
        <span>C</span>
        <i />
      </button>
      <nav aria-label="Primary navigation">
        {navigation.map((item) => (
          <button
            key={item.page}
            className={page === item.page ? 'nav-item active' : 'nav-item'}
            onClick={() => navigate(item.page)}
            aria-current={page === item.page ? 'page' : undefined}
          >
            <span className="nav-index">{item.index}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>
      <div className="sidebar-foot">C.01</div>
    </aside>
  )
}
