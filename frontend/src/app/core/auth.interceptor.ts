/** Attach bearer credentials and reset stale protected sessions. */
import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

import { AuthService } from './auth.service';

/** Add the memory-only bearer token and redirect after protected 401 responses.
 *
 * Args:
 *   request: The outgoing HTTP request.
 *   next: The remaining HTTP handler chain.
 * Returns: The intercepted response observable.
 */
export const authInterceptor: HttpInterceptorFn = (request, next) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const isAuthEndpoint = request.url.includes('/api/auth/login') || request.url.includes('/api/auth/verify');
  const token = auth.token();
  const authorizedRequest = token !== null && !isAuthEndpoint
    ? request.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
    : request;
  return next(authorizedRequest).pipe(catchError((error: HttpErrorResponse) => {
    if (error.status === 401 && !isAuthEndpoint) {
      auth.clearSession();
      void router.navigate(['/login']);
    }
    return throwError(() => error);
  }));
};
