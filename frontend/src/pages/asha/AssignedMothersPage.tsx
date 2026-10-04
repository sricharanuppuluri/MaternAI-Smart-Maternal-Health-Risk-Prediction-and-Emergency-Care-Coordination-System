import React from 'react';
import { Link } from 'react-router-dom';
import { Card, Badge, Button } from '../../components/common';

export const AssignedMothersPage: React.FC = () => {
  const sampleMothers = [
    { id: '1', name: 'Priya Sharma', age: 24, week: 24, risk: 'LOW', village: 'Rampur', nextVisit: 'Tomorrow' },
    { id: '2', name: 'Kavita Bai', age: 27, week: 32, risk: 'HIGH', village: 'Rampur', nextVisit: 'Urgent (Today)' },
    { id: '3', name: 'Sunita Devi', age: 29, week: 16, risk: 'MEDIUM', village: 'Kalyanpur', nextVisit: 'In 3 days' },
  ];

  return (
    <div className="portal-page assigned-mothers-page" role="region" aria-labelledby="mothers-title">
      <header className="page-header">
        <h1 id="mothers-title" className="page-title">Assigned Mothers Roster</h1>
        <p className="page-subtitle">
          List of expecting and postpartum mothers assigned to your sector.
        </p>
      </header>

      <Card title="Cohort Overview" subtitle="Authorized care cases under Row Level Security isolation">
        <div className="table-responsive">
          <table className="data-table" aria-label="Assigned Mothers Table">
            <thead>
              <tr>
                <th scope="col">Mother Name</th>
                <th scope="col">Age / Gestation</th>
                <th scope="col">Village Sector</th>
                <th scope="col">Screening Risk</th>
                <th scope="col">Next Follow-up</th>
                <th scope="col">Actions</th>
              </tr>
            </thead>
            <tbody>
              {sampleMothers.map((m) => (
                <tr key={m.id}>
                  <td className="font-bold">{m.name}</td>
                  <td>Age {m.age}, Week {m.week}</td>
                  <td>{m.village}</td>
                  <td>
                    <Badge
                      label={m.risk}
                      variant={m.risk === 'HIGH' ? 'danger' : m.risk === 'MEDIUM' ? 'warning' : 'success'}
                    />
                  </td>
                  <td>{m.nextVisit}</td>
                  <td>
                    <div className="flex gap-2">
                      <Link to={`/asha/mothers/${m.id}/timeline`}>
                        <Button variant="outline" size="sm">
                          View Timeline
                        </Button>
                      </Link>
                      <Link to={`/asha/mothers/${m.id}/assistant`}>
                        <Button variant="secondary" size="sm">
                          Care Assistant
                        </Button>
                      </Link>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
