import {
  SideNav,
  SideNavDivider,
  SideNavItems,
  SideNavLink,
} from '@carbon/react';
import { Chat, Help, Search } from '@carbon/icons-react';

// Primary side navigation (IBM Carbon UI Shell).
// Static links for the Phase 4B shell; destinations are wired in later phases.
export function AppSideNav() {
  return (
    <SideNav
      aria-label="Primary navigation"
      isFixedNav
      expanded
      isChildOfHeader={false}
    >
      <SideNavItems>
        <SideNavLink renderIcon={Chat} href="#" isActive>
          Ask
        </SideNavLink>
        <SideNavLink renderIcon={Search} href="#">
          Schema reference
        </SideNavLink>
        <SideNavDivider />
        <SideNavLink renderIcon={Help} href="#">
          Help
        </SideNavLink>
      </SideNavItems>
    </SideNav>
  );
}
