import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/common';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="not-found-container" role="main">
      <div className="not-found-card">
        <h1 className="not-found-code">404</h1>
        <h2 className="not-found-title">Page Not Found</h2>
        <p className="not-found-desc">
          The maternal health page or portal view you requested does not exist or has moved.
        </p>
        <Link to="/">
          <Button variant="primary">Return to Care Portal Home</Button>
        </Link>
      </div>
    </div>
  );
};
