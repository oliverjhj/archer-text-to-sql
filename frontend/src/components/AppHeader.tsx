import {
  Header,
  HeaderGlobalAction,
  HeaderGlobalBar,
  HeaderName,
  SkipToContent,
} from '@carbon/react';
import { Asleep, Help, Light } from '@carbon/icons-react';
import type { ThemeName } from '../hooks/useTheme';

interface AppHeaderProps {
  theme: ThemeName;
  onToggleTheme: () => void;
}

// Top application bar (IBM Carbon UI Shell).
export function AppHeader({ theme, onToggleTheme }: AppHeaderProps) {
  const switchingToLight = theme === 'dark';

  return (
    <Header aria-label="Archer Text-to-SQL">
      <SkipToContent />
      <HeaderName href="#" prefix="Archer">
        Text-to-SQL
      </HeaderName>
      <HeaderGlobalBar>
        {/*
          The label describes the theme you would switch TO, not the one you
          are in. Labelling it with the current state reads as a status
          display, and people click it expecting nothing to happen.
        */}
        <HeaderGlobalAction
          aria-label={switchingToLight ? 'Switch to light theme' : 'Switch to dark theme'}
          tooltipAlignment="end"
          onClick={onToggleTheme}
        >
          {switchingToLight ? <Light size={20} /> : <Asleep size={20} />}
        </HeaderGlobalAction>
        <HeaderGlobalAction aria-label="About" tooltipAlignment="end">
          <Help size={20} />
        </HeaderGlobalAction>
      </HeaderGlobalBar>
    </Header>
  );
}
