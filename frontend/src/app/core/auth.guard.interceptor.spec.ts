import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, provideRouter, Router, RouterStateSnapshot } from '@angular/router';

import { authGuard } from './auth.guard';
import { authInterceptor } from './auth.interceptor';
import { AuthService } from './auth.service';

describe('authentication route and HTTP boundaries', () => {
  let http: HttpTestingController | undefined;

  afterEach(() => http?.verify());

  it('returns a login URL tree when an unauthenticated visitor opens a protected route', () => {
    TestBed.configureTestingModule({ providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()] });
    http = TestBed.inject(HttpTestingController);

    const decision = TestBed.runInInjectionContext(() => authGuard({} as ActivatedRouteSnapshot, {} as RouterStateSnapshot));

    expect(TestBed.inject(Router).serializeUrl(decision as ReturnType<Router['createUrlTree']>)).toBe('/login');
  });

  it('allows a protected route when the current runtime has a token', () => {
    TestBed.configureTestingModule({ providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()] });
    http = TestBed.inject(HttpTestingController);
    TestBed.inject(AuthService).token.set('issued-token');

    expect(TestBed.runInInjectionContext(() => authGuard({} as ActivatedRouteSnapshot, {} as RouterStateSnapshot))).toBeTrue();
  });

  describe('authInterceptor', () => {
    let http: HttpTestingController;
    let client: HttpClient;
    let auth: AuthService;
    let router: Router;

    beforeEach(() => {
      TestBed.configureTestingModule({
        providers: [provideRouter([]), provideHttpClient(withInterceptors([authInterceptor])), provideHttpClientTesting()]
      });
      http = TestBed.inject(HttpTestingController);
      client = TestBed.inject(HttpClient);
      auth = TestBed.inject(AuthService);
      router = TestBed.inject(Router);
    });

    it('adds the memory token to a protected API request but never to an auth request', () => {
      auth.token.set('issued-token');
      client.get('/api/movies').subscribe();
      expect(http.expectOne('/api/movies').request.headers.get('Authorization')).toBe('Bearer issued-token');

      client.post('/api/auth/login', { mobile_number: '9876543210' }).subscribe();
      expect(http.expectOne('/api/auth/login').request.headers.has('Authorization')).toBeFalse();
    });

    it('clears a stale protected session and takes the visitor back to the accessible login page after a 401', () => {
      const navigate = spyOn(router, 'navigate').and.resolveTo(true);
      auth.token.set('expired-token');
      auth.pendingMobile.set('9876543210');
      client.get('/api/movies').subscribe({ error: () => undefined });

      http.expectOne('/api/movies').flush({ error: { message: 'expired' } }, { status: 401, statusText: 'Unauthorized' });

      expect(auth.isAuthenticated()).toBeFalse();
      expect(navigate).toHaveBeenCalledWith(['/login']);
    });
  });
});
