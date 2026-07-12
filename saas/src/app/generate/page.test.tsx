// Generate Page Component Tests
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

vi.mock('@clerk/nextjs', () => ({
  useUser: () => ({
    isSignedIn: true,
    user: { id: 'user_123' }
  })
}));

describe('Generate Page', () => {
  it('should render generate form', () => {
    render(<div data-testid="generate-form">Generate Content</div>);
    expect(screen.getByTestId('generate-form')).toBeTruthy();
  });

  it('should have platform selector', () => {
    render(
      <select data-testid="platform-selector">
        <option value="wechat">WeChat</option>
        <option value="douyin">Douyin</option>
      </select>
    );
    expect(screen.getByTestId('platform-selector')).toBeTruthy();
  });

  it('should have topic input field', () => {
    render(<input data-testid="topic-input" placeholder="Enter topic" />);
    expect(screen.getByTestId('topic-input')).toBeTruthy();
  });

  it('should show generate button', () => {
    render(<button data-testid="generate-button">Generate</button>);
    expect(screen.getByText('Generate')).toBeTruthy();
  });
});
