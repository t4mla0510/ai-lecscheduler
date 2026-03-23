// Sidebar + main content layout
import { useAppState } from '../data/store';

const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'data', label: 'Data Manager', icon: '📋' },
    { id: 'scheduler', label: 'GA Scheduler', icon: '🧬' },
    { id: 'timetable', label: 'Timetable', icon: '📅' },
];

export function Layout({ children }: { children: React.ReactNode }) {
    const { state, dispatch } = useAppState();

    return (
        <div className="layout">
            <aside className="sidebar">
                <div className="sidebar-header">
                    <div className="logo-icon">🎓</div>
                    <h1 className="sidebar-title">LecScheduler</h1>
                    <p className="sidebar-subtitle">Genetic Algorithm</p>
                </div>
                <nav className="nav">
                    {navItems.map(item => (
                        <button
                            key={item.id}
                            className={`nav-item ${state.currentPage === item.id ? 'active' : ''}`}
                            onClick={() => dispatch({ type: 'SET_PAGE', payload: item.id })}
                        >
                            <span className="nav-icon">{item.icon}</span>
                            <span className="nav-label">{item.label}</span>
                        </button>
                    ))}
                </nav>
                <div className="sidebar-footer">
                    <div className="status-indicator">
                        <span className={`status-dot ${state.gaStatus}`}></span>
                        <span className="status-text">
                            {state.gaStatus === 'idle' && 'Ready'}
                            {state.gaStatus === 'running' && 'Optimizing...'}
                            {state.gaStatus === 'completed' && 'Completed'}
                        </span>
                    </div>
                </div>
            </aside>
            <main className="main-content">
                {children}
            </main>
        </div>
    );
}
