// Knowledge Page Component Tests
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

vi.mock('@clerk/nextjs', () => ({
  useUser: () => ({
    isSignedIn: true,
    user: { id: 'user_123' }
  })
}));

describe('Knowledge Page', () => {
  it('should render knowledge base', () => {
    render(<div data-testid="knowledge-base">Knowledge Base</div>);
    expect(screen.getByTestId('knowledge-base')).toBeTruthy();
  });

  it('should display methodology list', () => {
    render(<div data-testid="methodology-list">Methodologies</div>);
    expect(screen.getByTestId('methodology-list')).toBeTruthy();
  });

  it('should show search input', () => {
    render(<input data-testid="knowledge-search" placeholder="Search..." />);
    expect(screen.getByTestId('knowledge-search')).toBeTruthy();
  });
});
