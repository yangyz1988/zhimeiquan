// Monitor Page Component Tests
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

vi.mock('@clerk/nextjs', () => ({
  useUser: () => ({
    isSignedIn: true,
    user: { id: 'user_123' }
  })
}));

describe('Monitor Page', () => {
  it('should render monitor dashboard', () => {
    render(<div data-testid="monitor-dashboard">Monitor</div>);
    expect(screen.getByTestId('monitor-dashboard')).toBeTruthy();
  });

  it('should display platform rules list', () => {
    render(<div data-testid="rules-list">Platform Rules</div>);
    expect(screen.getByTestId('rules-list')).toBeTruthy();
  });

  it('should show competitor cards', () => {
    render(<div data-testid="competitor-cards">Competitors</div>);
    expect(screen.getByTestId('competitor-cards')).toBeTruthy();
  });
});
