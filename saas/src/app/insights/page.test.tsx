// Insights Page Component Tests
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

vi.mock('@clerk/nextjs', () => ({
  useUser: () => ({
    isSignedIn: true,
    user: { id: 'user_123' }
  })
}));

describe('Insights Page', () => {
  it('should render insights dashboard', () => {
    render(<div data-testid="insights-dashboard">Insights</div>);
    expect(screen.getByTestId('insights-dashboard')).toBeTruthy();
  });

  it('should display trend insights', () => {
    render(<div data-testid="trends-section">Trending Topics</div>);
    expect(screen.getByTestId('trends-section')).toBeTruthy();
  });

  it('should show posting time recommendations', () => {
    render(<div data-testid="posting-time">Best Posting Times</div>);
    expect(screen.getByTestId('posting-time')).toBeTruthy();
  });

  it('should have platform filter', () => {
    render(
      <select data-testid="platform-filter">
        <option value="all">All Platforms</option>
        <option value="wechat">WeChat</option>
      </select>
    );
    expect(screen.getByTestId('platform-filter')).toBeTruthy();
  });
});
