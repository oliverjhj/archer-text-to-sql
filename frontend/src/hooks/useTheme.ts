import { useCallback, useEffect, useState } from 'react';

export type ThemeName = 'dark' | 'light';

/**
 * The key is shared with the login page's inline script, so a choice made on
 * either side carries across signing in. Changing it here means changing it in
 * backend/templates/login.html too.
 */
const STORAGE_KEY = 'archer-theme';

/** Dark, because the application is dark and that is the intended look. */
const DEFAULT_THEME: ThemeName = 'dark';

function readStoredTheme(): ThemeName {
  try {
    return window.localStorage.getItem(STORAGE_KEY) === 'light' ? 'light' : DEFAULT_THEME;
  } catch {
    // Private browsing, or storage disabled. The default is not a failure.
    return DEFAULT_THEME;
  }
}

/**
 * Current theme, plus a way to flip it.
 *
 * The `data-theme` attribute on the root element is kept in step so that plain
 * CSS can respond to the theme as well as Carbon's own components - the login
 * page uses the same attribute, so the two halves of the application agree
 * without sharing a stylesheet.
 */
export function useTheme(): { theme: ThemeName; toggle: () => void } {
  const [theme, setTheme] = useState<ThemeName>(readStoredTheme);

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'light') {
      root.setAttribute('data-theme', 'light');
    } else {
      root.removeAttribute('data-theme');
    }

    try {
      window.localStorage.setItem(STORAGE_KEY, theme);
    } catch {
      // Preference will not persist; the toggle still works for this session.
    }
  }, [theme]);

  const toggle = useCallback(() => {
    setTheme((current) => (current === 'light' ? 'dark' : 'light'));
  }, []);

  return { theme, toggle };
}
