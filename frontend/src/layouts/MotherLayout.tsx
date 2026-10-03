import React from 'react';
import { Outlet, NavLink } from 'react-router-dom';

export const MotherLayout: React.FC = () => {
  return (
    <div className="portal-container mother-portal">
      <div className="portal-subnav" role="navigation" aria-label="Mother Portal Navigation">
        <div className="subnav-inner">
          <span className="portal-badge badge-mother">Mother Portal</span>
          <div className="portal-links">
            <NavLink
              to="/mother"
              end
              className={({ isActive }) => `portal-link ${isActive ? 'active' : ''}`}
            >
              Dashboard
            </NavLink>
            <NavLink
              to="/mother/health-entry"
              className={({ isActive }) => `portal-link ${isActive ? 'active' : ''}`}
            >
              Health Entry
            </NavLink>
            <NavLink
              to="/mother/risk-timeline"
              className={({ isActive }) => `portal-link ${isActive ? 'active' : ''}`}
            >
              Risk Timeline
            </NavLink>
          </div>
        </div>
      </div>

      <div className="portal-content">
        <Outlet />
      </div>
    </div>
  );
};
