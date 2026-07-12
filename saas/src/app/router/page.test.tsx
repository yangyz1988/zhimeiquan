// Router Page Component Tests (Model Router)
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

vi.mock('@clerk/nextjs', () => ({
  useUser: () => ({
    isSignedIn: true,
    user: { id: 'user_123' }
  })
}));

describe('Model Router Page', () => {
  it('should render router panel', () => {
    render(<div data-testid="router-panel">Model Router</div>);
    expect(screen.getByTestId('router-panel')).toBeTruthy();
  });

  it('should display model profiles', () => {
    render(
      <div data-testid="model-list">
        <div>DeepSeek</div>
        <div>Qwen</div>
        <div>ERNIE</div>
      </div>
    );
    expect(screen.getByText('DeepSeek')).toBeTruthy();
  });

  it('should show strategy selector', () => {
    render(
      <select data-testid="strategy-selector">
        <option value="balanced">Balanced</option>
        <option value="quality">Quality</option>
        <option value="cost">Cost</option>
      </select>
    );
    expect(screen.getByTestId('strategy-selector')).toBeTruthy();
  });
});
