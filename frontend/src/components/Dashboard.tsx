// Dashboard with summary cards and quick actions
import { useAppState } from '../data/store';

export function Dashboard() {
    const { state, dispatch } = useAppState();

    const totalUnits = state.courses.reduce((sum, c) => sum + c.unitsPerWeek, 0);

    const cards = [
        { label: 'Lecturers', value: state.lecturers.length, color: '#1f5ca9', sub: 'Faculty members' },
        { label: 'Courses', value: state.courses.length, color: '#00afef', sub: `${totalUnits} units/week total` },
        { label: 'Rooms', value: state.rooms.length, color: '#0ea5e9', sub: 'Available rooms' },
    ];

    return (
        <div className="dashboard">
            <div className="page-header">
                <h2 className="page-title">Dashboard</h2>
                <p className="page-description">Overview of lecturer timetable scheduling system</p>
            </div>

            <div className="cards-grid">
                {cards.map((card, i) => (
                    <div key={i} className="summary-card" style={{ '--card-accent': card.color } as React.CSSProperties}>
                        <div className="card-info">
                            <span className="card-value">{card.value}</span>
                            <span className="card-label">{card.label}</span>
                            <span className="card-sub">{card.sub}</span>
                        </div>
                        <div className="card-glow" style={{ background: `radial-gradient(circle, ${card.color}22 0%, transparent 70%)` }}></div>
                    </div>
                ))}
            </div>

            <div className="quick-actions">
                <h3 className="section-title">Quick Actions</h3>
                <div className="actions-row">
                    <button className="action-btn primary" onClick={() => dispatch({ type: 'SET_PAGE', payload: 'scheduler' })}>
                        <span className="action-icon">🚀</span>
                        <span>Generate Timetable</span>
                    </button>
                    <button className="action-btn secondary" onClick={() => dispatch({ type: 'SET_PAGE', payload: 'data' })}>
                        <span className="action-icon">✏️</span>
                        <span>Manage Data</span>
                    </button>
                    {state.timetable && (
                        <button className="action-btn accent" onClick={() => dispatch({ type: 'SET_PAGE', payload: 'timetable' })}>
                            <span className="action-icon">👁️</span>
                            <span>View Timetable</span>
                        </button>
                    )}
                </div>
            </div>

            <div className="info-panel">
                <h3 className="section-title">How It Works</h3>
                <div className="steps-grid">
                    <div className="step-card">
                        <div className="step-number">1</div>
                        <h4>Input Data</h4>
                        <p>Add lecturers, courses, and rooms with their constraints and preferences.</p>
                    </div>
                    <div className="step-card">
                        <div className="step-number">2</div>
                        <h4>Generate</h4>
                        <p>Run the GA algorithm to optimize and generate a minimize conflict timetable.</p>
                    </div>
                    <div className="step-card">
                        <div className="step-number">3</div>
                        <h4>Review</h4>
                        <p>View the optimized timetable grid with color-coded courses and conflict reports.</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
