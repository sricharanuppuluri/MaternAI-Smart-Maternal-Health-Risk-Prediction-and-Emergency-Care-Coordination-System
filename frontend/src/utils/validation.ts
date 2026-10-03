/**
 * Form and input validation utilities for MaternAI.
 */

export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email.trim());
}

export function isValidIndianPhone(phone: string): boolean {
  // Allows optional +91 and 10 digits
  const phoneRegex = /^(\+91[\s-]?)?[6789]\d{9}$/;
  return phoneRegex.test(phone.trim().replace(/\s+/g, ''));
}

export function isNumericInRange(
  val: number | string | undefined,
  min: number,
  max: number
): boolean {
  if (val === undefined || val === '') return false;
  const num = typeof val === 'string' ? parseFloat(val) : val;
  return !isNaN(num) && num >= min && num <= max;
}
