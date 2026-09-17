import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';

import { AuthService } from './auth.service';

describe('AuthService', () => {
  let auth: AuthService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    auth = TestBed.inject(AuthService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('requests an OTP and makes the verified mobile available to the OTP journey', () => {
    auth.requestOtp('9876543210').subscribe();

    const request = http.expectOne('/api/auth/login');
    expect(request.request.body).toEqual({ mobile_number: '9876543210' });
    request.flush({ authentication_state: 'otp_required', mobile_number: '9876543210' });

    expect(auth.pendingMobile()).toBe('9876543210');
    expect(auth.isAuthenticated()).toBeFalse();
  });

  it('stores the backend-issued bearer token only after successful OTP verification', () => {
    auth.requestOtp('9876543210').subscribe();
    http.expectOne('/api/auth/login').flush({ authentication_state: 'otp_required', mobile_number: '9876543210' });

    auth.verifyOtp('1234').subscribe();
    const request = http.expectOne('/api/auth/verify');
    expect(request.request.body).toEqual({ mobile_number: '9876543210', otp: '1234' });
    request.flush({ access_token: 'issued-token', token_type: 'bearer', expires_in: 1800, claims: {} });

    expect(auth.isAuthenticated()).toBeTrue();
    expect(auth.token()).toBe('issued-token');
  });

  it('rejects OTP verification before a mobile number has been requested', () => {
    expect(() => auth.verifyOtp('1234')).toThrowError('A mobile number is required before OTP verification.');
  });

  it('clears the memory-only token so a refreshed runtime starts unauthenticated', () => {
    auth.token.set('issued-token');
    auth.pendingMobile.set('9876543210');

    auth.clearSession();

    expect(auth.isAuthenticated()).toBeFalse();
    expect(auth.token()).toBeNull();
    expect(auth.pendingMobile()).toBeNull();
  });
});
