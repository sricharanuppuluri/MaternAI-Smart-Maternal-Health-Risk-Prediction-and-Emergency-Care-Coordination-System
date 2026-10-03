import React from 'react';
import { Outlet, NavLink } from 'react-router-dom';

export const AshaLayout: React.FC = () => {
  return (
    <div className="portal-container asha-portal">
      <div className="portal-subnav" role="navigation" aria-label="ASHA Portal Navigation">
        <div className="subnav-inner">
          <span className="portal-badge badge-asha">ASHA Worker Portal</span>
          <div className="portal-links">
            <NavLink
              to="/asha"
              end
              className={({ isActive }) => `portal-link ${isActive ? 'active' : ''}`}
            >
              Case Dashboard
            </NavLink>
            <NavLink
              to="/asha/alerts"
              className={({ isActive }) => `portal-link ${isActive ? 'active' : ''}`}
            >
              Alerts Queue
            </NavLink>
            <NavLink
              to="/asha/mothers"
              className={({ isActive }) => `portal-link ${isActive ? 'active' : ''}`}
            >
              Assigned Mothers
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
