import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from '../components/layout/Sidebar';
import Navbar from '../components/layout/Navbar';
import { violationService } from '../services/violationService';

const AppLayout = () => {
  const [signalState, setSignalState] = useState('GREEN');

  useEffect(() => {
    // Poll signal state or default to GREEN
    const fetchSignal = async () => {
      try {
        const res = await violationService.getSignalState();
        if (res.data?.state) {
          setSignalState(res.data.state);
        }
      } catch (err) {
        // Fallback default
      }
    };
    fetchSignal();
    const interval = setInterval(fetchSignal, 6000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex min-h-screen bg-[#0b0f19]">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar signalState={signalState} />
        <main className="flex-1 p-8 overflow-y-auto">
          <Outlet context={{ signalState, setSignalState }} />
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
