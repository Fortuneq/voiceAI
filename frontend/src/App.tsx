import React from 'react';
import { AuthProvider } from './contexts/AuthContext';
import { Dashboard, ProtectedRoute } from './components';
import './index.css';

const App: React.FC = () => {
  return (
    <div className="App">
      <AuthProvider>
        <ProtectedRoute>
          <Dashboard />
        </ProtectedRoute>
      </AuthProvider>
    </div>
  );
};

export default App;