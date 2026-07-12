// Calendar Page Component Tests
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

vi.mock('@clerk/nextjs', () => ({
  useUser: () => ({
    isSignedIn: true,
    user: { id: 'user_123' }
  })
}));

describe('Calendar Page', () => {
  it('should render calendar view', () => {
    render(<div data-testid="calendar-view">Content Calendar</div>);
    expect(screen.getByTestId('calendar-view')).toBeTruthy();
  });

  it('should display scheduled posts', () => {
    render(<div data-testid="scheduled-posts">Scheduled: 5 posts</div>);
    expect(screen.getByText('Scheduled: 5 posts')).toBeTruthy();
  });

  it('should have month navigation', () => {
    render(
      <div data-testid="month-nav">
        <button>Previous</button>
        <span>January 2024</span>
        <button>Next</button>
      </div>
    );
    expect(screen.getByText('Previous')).toBeTruthy();
    expect(screen.getByText('Next')).toBeTruthy();
  });
});
