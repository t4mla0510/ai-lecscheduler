// Conflict Panel: displays constraint violations from the backend GA result
import { useAppState } from '../data/store';

export function ConflictPanel() {
    const { state } = useAppState();

    if (!state.timetable || state.timetable.length === 0) return null;

    const hard = state.hardConstraints;
    const soft = state.softConstraints;

    const hasHardViolations = hard && hard.total_violations > 0;
    const hasSoftIssues = soft && Object.values(soft.by_type).some(v => v < 0);

    if (!hasHardViolations && !hasSoftIssues) {
        return (
            <div className="conflict-panel success">
                <div className="conflict-header">
                    <span className="conflict-icon">✅</span>
                    <h3>No Conflicts</h3>
                </div>
                <p>The generated timetable has no constraint violations. All constraints are satisfied.</p>
            </div>
        );
    }

    return (
        <div className="conflict-panel">
            <div className="conflict-header">
                <span className="conflict-icon">⚡</span>
                <h3>Constraint Report</h3>
                <span className="fitness-badge">Fitness: {state.bestFitness.toFixed(4)}</span>
            </div>

            {hasHardViolations && hard && (
                <>
                    <h4 style={{ margin: '12px 0 8px', color: '#ef4444' }}>
                        Hard Constraints ({hard.total_violations} violations)
                    </h4>
                    <div className="conflict-list">
                        {Object.entries(hard.by_type)
                            .filter(([, count]) => count > 0)
                            .map(([type, count]) => (
                                <div key={type} className="conflict-item severity-high">
                                    <span className="conflict-item-icon">⚠️</span>
                                    <div className="conflict-item-info">
                                        <span className="conflict-item-label">
                                            {type.replace(/_/g, ' ')}
                                        </span>
                                    </div>
                                    <span className="conflict-count">{count}</span>
                                </div>
                            ))}
                    </div>
                    {hard.details.length > 0 && (
                        <div style={{ marginTop: '8px', fontSize: '12px', color: '#94a3b8' }}>
                            {hard.details.slice(0, 20).map((d, i) => (
                                <div key={i}>• {d}</div>
                            ))}
                            {hard.details.length > 20 && (
                                <div>...and {hard.details.length - 20} more</div>
                            )}
                        </div>
                    )}
                </>
            )}

            {soft && (
                <>
                    <h4 style={{ margin: '12px 0 8px', color: '#f59e0b' }}>
                        Soft Constraints (score: {soft.total_score})
                    </h4>
                    <div className="conflict-list">
                        {Object.entries(soft.by_type).map(([type, score]) => (
                            <div key={type} className={`conflict-item ${score >= 0 ? 'severity-low' : 'severity-medium'}`}>
                                <span className="conflict-item-icon">{score >= 0 ? '✅' : '💡'}</span>
                                <div className="conflict-item-info">
                                    <span className="conflict-item-label">
                                        {type.replace(/_/g, ' ')}
                                    </span>
                                </div>
                                <span className="conflict-count">{score >= 0 ? '+' : ''}{score}</span>
                            </div>
                        ))}
                    </div>
                </>
            )}
        </div>
    );
}
