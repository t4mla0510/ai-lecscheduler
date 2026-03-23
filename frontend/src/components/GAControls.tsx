/* eslint-disable @typescript-eslint/no-explicit-any */
import { useRef, useCallback, useState } from "react";
import { useAppState } from "../data/store";
import type { ScheduleRequest } from "../data/types";
import { GAVisualizer } from "./GAVisualizer";
import type { GenStat } from "./GAVisualizer";

interface RangeFieldProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  disabled?: boolean;
  onChange: (val: number) => void;
  suffix?: string;
}

function RangeField({ label, value, min, max, step = 1, disabled, onChange, suffix = "" }: RangeFieldProps) {
  const displayValue = step < 1 ? value.toFixed(2) : value;
  return (
    <div className="param-group">
      <label className="param-label">
        {label}
        <span className="param-value">{displayValue}{suffix}</span>
      </label>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(+e.target.value)}
      />
    </div>
  );
}

interface SelectFieldProps {
  label: string;
  value: string;
  options: { value: string; label: string }[];
  disabled?: boolean;
  onChange: (val: string) => void;
}

function SelectField({ label, value, options, disabled, onChange }: SelectFieldProps) {
  return (
    <div className="param-group">
      <label className="param-label">{label}</label>
      <select
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}

interface NumberFieldProps {
  label: string;
  value: number;
  disabled?: boolean;
  onChange: (val: number) => void;
}

function NumberField({ label, value, disabled, onChange }: NumberFieldProps) {
  return (
    <div className="param-group">
      <label className="param-label">{label}</label>
      <input
        type="number"
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(+e.target.value)}
      />
    </div>
  );
}

export function GAControls() {
  const { state, dispatch } = useAppState();
  const config = state.gaConfig;

  const abortControllerRef = useRef<AbortController | null>(null);
  const lastUpdateRef = useRef(0);
  const genRef = useRef(0);
  const histRef = useRef<GenStat[]>([]);

  const [history, setHistory] = useState<GenStat[]>([]);
  const [visGeneration, setVisGeneration] = useState(0);

  const disabled = state.gaStatus === "running";
  const last = history[history.length - 1];

  /* config helpers */
  const setConfig = useCallback(
    (updater: (prev: ScheduleRequest) => ScheduleRequest) =>
      dispatch({ type: "SET_GA_CONFIG", payload: updater(config) }),
    [dispatch, config]
  );

  const updateGA = (p: Partial<ScheduleRequest["ga"]>) =>
    setConfig((c) => ({ ...c, ga: { ...c.ga, ...p } }));

  const updateSelection = (p: Partial<ScheduleRequest["selection"]>) =>
    setConfig((c) => ({ ...c, selection: { ...c.selection, ...p } }));

  const updateCrossover = (p: Partial<ScheduleRequest["crossover"]>) =>
    setConfig((c) => ({ ...c, crossover: { ...c.crossover, ...p } }));

  const updateMutation = (p: Partial<ScheduleRequest["mutation"]>) =>
    setConfig((c) => ({ ...c, mutation: { ...c.mutation, ...p } }));

  const updateFitness = (p: Partial<ScheduleRequest["fitness"]>) =>
    setConfig((c) => ({ ...c, fitness: { ...c.fitness, ...p } }));

  /* Run GA*/
  const handleRun = useCallback(async () => {
    // Reset local state
    setHistory([]);
    setVisGeneration(0);
    histRef.current = [];
    genRef.current = 0;
    lastUpdateRef.current = Date.now();

    dispatch({ type: "SET_GA_STATUS", payload: "running" });
    dispatch({ type: "SET_CURRENT_GENERATION", payload: 0 });

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/schedule`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
        signal: controller.signal
      });

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const data = JSON.parse(line.slice(6));

            if (data.type === "progress") {
              const stat: GenStat = {
                generation: data.generation,
                best: data.best,
                avg: data.avg,
                worst: data.worst,
                elites: 0,
                mutants: 0,
                crossovers: 0
              };

              // Always update the ref (data source)
              histRef.current.push(stat);
              genRef.current = data.generation;

              // Throttle UI updates to once every 100ms
              const now = Date.now();
              if (now - lastUpdateRef.current > 100) {
                setHistory([...histRef.current]);
                setVisGeneration(data.generation);
                dispatch({ type: "SET_CURRENT_GENERATION", payload: data.generation });
                lastUpdateRef.current = now;
              }
            }

            if (data.type === "final") {
              const result = data;

              const bestFitness =
                typeof result.best_fitness === "number"
                  ? result.best_fitness
                  : result.best_fitness?.hard_score ??
                  result.best_fitness?.fitness ??
                  0;

              dispatch({
                type: "SET_TIMETABLE",
                payload: result.schedule.map((s: any) => ({
                  courseId: s.courseId,
                  courseName: s.courseName,
                  lecturerId: s.lecturerId,
                  lecturerName: s.lecturerName,
                  roomId: s.roomId,
                  roomName: s.roomName,
                  timeslotId: s.timeslotId,
                  units: s.units,
                })),
              });

              dispatch({ type: "SET_BEST_FITNESS", payload: bestFitness });
              dispatch({
                type: "SET_HARD_CONSTRAINTS",
                payload: result.hard_constraints ?? [],
              });
              dispatch({
                type: "SET_SOFT_CONSTRAINTS",
                payload: result.soft_constraints ?? [],
              });
              
              dispatch({ type: "SET_GA_STATUS", payload: "completed" });

              // Final UI sync
              setHistory([...histRef.current]);
              setVisGeneration(genRef.current);
            }
          } catch (err) {
            console.error("Error parsing stream message:", err);
          }
        }
      }
    } catch (err: any) {
      if (err.name === "AbortError") {
        console.log("GA run aborted", err);
      } else {
        console.error("GA run error:", err);
        dispatch({ type: "SET_GA_STATUS", payload: "idle" });
      }
    } finally {
      abortControllerRef.current = null;
    }
  }, [config, dispatch]);

  /* Stop and Reset */
  const handleStop = useCallback(() => {
    abortControllerRef.current?.abort();
    dispatch({ type: "SET_GA_STATUS", payload: "idle" });
  }, [dispatch]);

  // reset handler
  const handleReset = useCallback(() => {
    abortControllerRef.current?.abort();

    setHistory([]);
    setVisGeneration(0);
    histRef.current = [];
    genRef.current = 0;

    dispatch({ type: "RESET_GA" });
  }, [dispatch]);

  return (
    <div className="ga-controls">
      <header className="page-header">
        <h2 className="page-title">GA Scheduler</h2>
        <p className="page-description">
          Configure and run the genetic algorithm, then explore each step in the visualizer
        </p>
      </header>

      <div className="ga-layout">
        {/* LEFT — params */}
        <div className="ga-params">
          <section className="config-section">
            <h3 className="section-title">Population</h3>
            <RangeField label="Population Size"
              min={10}
              max={500}
              step={10}
              value={config.ga.pop_size}
              disabled={disabled}
              onChange={pop_size => updateGA({ pop_size })}
            />
            <RangeField
              label="Max Generations"
              min={50}
              max={5000}
              step={50}
              value={config.ga.max_generations}
              disabled={disabled}
              onChange={max_generations => updateGA({ max_generations })}
            />
            <RangeField
              label="Max Time"
              min={10}
              max={60}
              step={5}
              value={config.ga.max_time_seconds}
              suffix="s" disabled={disabled}
              onChange={max_time_seconds => updateGA({ max_time_seconds })}
            />
            <RangeField
              label="Elitism Rate"
              min={0}
              max={0.1}
              step={0.01}
              value={config.ga.elitism_rate}
              disabled={disabled}
              onChange={elitism_rate => updateGA({ elitism_rate })}
            />
          </section>

          <section className="config-section">
            <h3 className="section-title">Selection</h3>
            <SelectField
              label="Method"
              value={config.selection.method}
              disabled={disabled}
              onChange={method => updateSelection({ method })}
              options={[
                { value: "tournament", label: "Tournament" },
                { value: "roulette", label: "Roulette" },
                { value: "rank", label: "Rank" },
                { value: "elimination", label: "Elimination" },
              ]}
            />
            {config.selection.method === "tournament" && (
              <RangeField label="Tournament K" min={2} max={10} value={config.selection.tournament_k} disabled={disabled} onChange={tournament_k => updateSelection({ tournament_k })} />
            )}
          </section>

          <section className="config-section">
            <h3 className="section-title">Crossover</h3>
            <SelectField
              label="Method"
              value={config.crossover.method}
              disabled={disabled}
              onChange={method => updateCrossover({ method })}
              options={[
                { value: "single_point", label: "Single Point" },
                { value: "two_point", label: "Two Point" },
                { value: "multi_point", label: "Multi Point" },
                { value: "uniform", label: "Uniform" },
              ]}
            />
            {config.crossover.method === "multi_point" && (
              <RangeField label="N Points" min={1} max={10} value={config.crossover.n_points} disabled={disabled} onChange={n_points => updateCrossover({ n_points })} />
            )}
            <RangeField label="Rate" min={0} max={1} step={0.05} value={config.crossover.rate} disabled={disabled} onChange={rate => updateCrossover({ rate })} />
          </section>

          <section className="config-section">
            <h3 className="section-title">Mutation</h3>
            <SelectField
              label="Method"
              value={config.mutation.method}
              disabled={disabled}
              onChange={method => updateMutation({ method })}
              options={[
                { value: "random", label: "Random" },
                { value: "swap", label: "Swap" },
                { value: "creep", label: "Creep" },
                { value: "heuristic", label: "Heuristic" },
              ]}
            />
            <RangeField label="Rate" min={0} max={1} step={0.01} value={config.mutation.rate} disabled={disabled} onChange={rate => updateMutation({ rate })} />
          </section>

          <section className="config-section">
            <h3 className="section-title">Fitness</h3>
            <SelectField
              label="Method"
              value={config.fitness.method}
              disabled={disabled}
              onChange={method => updateFitness({ method })}
              options={[
                { value: "alpha_beta", label: "Alpha Beta" },
                { value: "penalty", label: "Penalty" },
                { value: "weighted", label: "Weighted" },
                { value: "lexicographic", label: "Lexicographic" },
              ]}
            />
            {config.fitness.method === "alpha_beta" && (
              <>
                <NumberField label="Alpha" value={config.fitness.alpha} disabled={disabled} onChange={alpha => updateFitness({ alpha })} />
                <NumberField label="Beta" value={config.fitness.beta} disabled={disabled} onChange={beta => updateFitness({ beta })} />
              </>
            )}
            {config.fitness.method === "penalty" && (
              <>
                <NumberField label="Base Score" value={config.fitness.base_score} disabled={disabled} onChange={base_score => updateFitness({ base_score })} />
                <NumberField label="Hard Penalty" value={config.fitness.hard_penalty} disabled={disabled} onChange={hard_penalty => updateFitness({ hard_penalty })} />
                <NumberField label="Soft Bonus" value={config.fitness.soft_bonus} disabled={disabled} onChange={soft_bonus => updateFitness({ soft_bonus })} />
              </>
            )}
          </section>

          <div className="control-buttons">
            {state.gaStatus !== "running" && <button className="btn-run" onClick={handleRun}>🚀 Run GA</button>}
            {state.gaStatus === "running" && <button className="btn-stop" onClick={handleStop}>⏹ Stop</button>}
            <button className="btn-reset" onClick={handleReset}>🔄 Reset</button>
          </div>

          {state.gaStatus === "completed" && (
            <div className="status-card completed">
              <div className="status-icon">✅</div>
              <div className="status-info">
                <div className="status-title">Run Completed</div>
                <div className="status-details">
                  Fitness: <strong>{state.bestFitness.toFixed(4)}</strong> · Generations: <strong>{state.currentGeneration}</strong>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* RIGHT — fitness chart */}
        <div className="ga-viz-panel">
          <GAVisualizer
            history={history}
            generation={visGeneration}
            status={state.gaStatus}
          />
          {last ? (
            <div className="viz-stats">
              <div className="viz-stat">
                <span className="viz-stat-label">Gen</span>
                <span className="viz-stat-value">{last.generation}</span>
              </div>
              <div className="viz-stat">
                <span className="viz-stat-label">
                  {config.fitness.method === "lexicographic" ? "Min Violations" : "Best Fitness"}
                </span>
                <span className="viz-stat-value" style={{ color: "#1f5ca9" }}>
                  {config.fitness.method === "lexicographic" ? Math.abs(last.best).toFixed(0) : last.best.toFixed(4)}
                </span>
              </div>
              <div className="viz-stat">
                <span className="viz-stat-label">
                  {config.fitness.method === "lexicographic" ? "Avg Violations" : "Avg Fitness"}
                </span>
                <span className="viz-stat-value" style={{ color: "#00afef" }}>
                  {config.fitness.method === "lexicographic" ? Math.abs(last.avg).toFixed(1) : last.avg.toFixed(4)}
                </span>
              </div>
              <div className="viz-stat">
                <span className="viz-stat-label">Diversity</span>
                <span className="viz-stat-value">{(last.best - last.worst).toFixed(4)}</span>
              </div>
              <div className="viz-stat">
                <span className="viz-stat-label">Elites</span>
                <span className="viz-stat-value">{last.elites}</span>
              </div>
            </div>
          ) : (
            <div className="viz-empty">
              <div className="viz-empty-icon">📈</div>
              <p>Press <strong>Run GA</strong> to watch fitness converge across generations</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
