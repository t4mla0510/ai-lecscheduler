import { useEffect } from 'react';
import { AppProvider, useAppState } from './data/store';
import { Layout } from './components/Layout';
import { Dashboard } from './components/Dashboard';
import { DataManager } from './components/DataManager';
import { GAControls } from './components/GAControls';
import { TimetableGrid } from './components/TimetableGrid';
import { lecturerApi } from './api/lecturerApi';
import { courseApi } from './api/courseApi';
import { roomApi } from './api/roomApi';
import { timeslotApi } from './api/timeslotApi';
import './index.css';

function PageRouter() {
  const { state } = useAppState();

  switch (state.currentPage) {
    case 'dashboard':
      return <Dashboard />;
    case 'data':
      return <DataManager />;
    case 'scheduler':
      return <GAControls />;
    case 'timetable':
      return <TimetableGrid />;
    default:
      return <Dashboard />;
  }
}

export function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}

function AppContent() {
  const { dispatch } = useAppState();

  useEffect(() => {
    Promise.all([
      lecturerApi.getAll(),
      courseApi.getAll(),
      roomApi.getAll(),
      timeslotApi.getAll(),
    ]).then(([lecRes, courseRes, roomRes, tsRes]) => {
      dispatch({ type: 'SET_LECTURERS', payload: lecRes.data });
      dispatch({ type: 'SET_COURSES', payload: courseRes.data });
      dispatch({ type: 'SET_ROOMS', payload: roomRes.data });
      dispatch({ type: 'SET_TIMESLOTS', payload: tsRes.data });
    });
  }, [dispatch]);

  return (
    <Layout>
      <PageRouter />
    </Layout>
  );
}

export default App;

