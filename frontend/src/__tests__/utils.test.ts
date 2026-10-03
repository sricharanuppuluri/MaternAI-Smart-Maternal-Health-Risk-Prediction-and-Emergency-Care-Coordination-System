import { describe, it, expect } from 'vitest';
import {
  formatDate,
  getRiskBadgeClass,
  getAlertBadgeClass,
} from '../utils/formatters';
import {
  isValidEmail,
  isValidIndianPhone,
  isNumericInRange,
} from '../utils/validation';

describe('formatters', () => {
  it('formats dates safely', () => {
    expect(formatDate(undefined)).toBe('—');
    expect(formatDate('')).toBe('—');
    const formatted = formatDate('2026-10-03T10:00:00Z');
    expect(formatted).toContain('2026');
  });

  it('maps maternal risk levels to badge classes', () => {
    expect(getRiskBadgeClass('LOW')).toBe('badge-success');
    expect(getRiskBadgeClass('MEDIUM')).toBe('badge-warning');
    expect(getRiskBadgeClass('HIGH')).toBe('badge-danger');
    expect(getRiskBadgeClass(undefined)).toBe('badge-neutral');
  });

  it('maps alert severity to badge classes', () => {
    expect(getAlertBadgeClass('CRITICAL')).toBe('badge-critical');
    expect(getAlertBadgeClass('HIGH')).toBe('badge-danger');
    expect(getAlertBadgeClass('MEDIUM')).toBe('badge-warning');
    expect(getAlertBadgeClass('LOW')).toBe('badge-info');
    expect(getAlertBadgeClass(undefined)).toBe('badge-neutral');
  });
});

describe('validation', () => {
  it('validates email addresses accurately', () => {
    expect(isValidEmail('mother@maternai.org')).toBe(true);
    expect(isValidEmail('asha.worker@subcenter.gov.in')).toBe(true);
    expect(isValidEmail('invalid-email')).toBe(false);
    expect(isValidEmail('')).toBe(false);
  });

  it('validates Indian 10-digit mobile numbers', () => {
    expect(isValidIndianPhone('9876543210')).toBe(true);
    expect(isValidIndianPhone('+91 9876543210')).toBe(true);
    expect(isValidIndianPhone('+919876543210')).toBe(true);
    expect(isValidIndianPhone('123456')).toBe(false);
    expect(isValidIndianPhone('0123456789')).toBe(false);
  });

  it('validates numeric ranges for vital parameters', () => {
    expect(isNumericInRange(120, 60, 200)).toBe(true);
    expect(isNumericInRange('120', 60, 200)).toBe(true);
    expect(isNumericInRange(250, 60, 200)).toBe(false);
    expect(isNumericInRange(40, 60, 200)).toBe(false);
    expect(isNumericInRange('', 60, 200)).toBe(false);
  });
});
