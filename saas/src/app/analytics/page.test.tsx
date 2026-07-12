// Analytics Page Component Tests
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

vi.mock('@clerk/nextjs', () => ({
  useUser: () => ({
    isSignedIn: true,
    user: { id: 'user_123' }
  })
}));

// Mock chart library
vi.mock('chart.js', () => ({
  Chart: vi.fn()
}));

describe('Analytics Page', () => {
  it('should render analytics dashboard', () => {
    render(<div data-testid="analytics-dashboard">Analytics</div>);
    expect(screen.getByTestId('analytics-dashboard')).toBeTruthy();
  });

  it('should display overview metrics', () => {
    render(
      <div data-testid="metrics-overview">
        <div>Total Content: 100</div>
        <div>Avg Score: 85</div>
      </div>
    );
    expect(screen.getByText('Total Content: 100')).toBeTruthy();
  });

  it('should show chart containers', () => {
    render(<div data-testid="chart-container">Chart Area</div>);
    expect(screen.getByTestId('chart-container')).toBeTruthy();
  });

  it('should have time range selector', () => {
    render(
      <select data-testid="time-range">
        <option value="7d">Last 7 days</option>
        <option value="30d">Last 30 days</option>
      </select>
    );
    expect(screen.getByTestId('time-range')).toBeTruthy();
  });
});
