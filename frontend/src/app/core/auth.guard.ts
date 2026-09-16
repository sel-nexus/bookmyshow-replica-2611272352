/** Gate protected routes behind the memory-only session. */
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthService } from './auth.service';

/** Redirect unauthenticated navigation to the login form.
 *
 * Returns: A navigation decision or login URL tree.
 */
export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  return auth.isAuthenticated() ? true : inject(Router).createUrlTree(['/login']);
};
