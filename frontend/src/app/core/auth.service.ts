/** Manage the deliberately memory-only authentication session. */
import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

import { environment } from '../../environments/environment';

interface LoginResponse { authentication_state: 'otp_required'; mobile_number: string; }
interface VerifyResponse { access_token: string; token_type: 'bearer'; expires_in: number; user: { id: string; mobile_number: string }; }

/** Coordinate API authentication while retaining no browser-persistent token. */
@Injectable({ providedIn: 'root' })
export class AuthService {
  /** Hold the current token only for this JavaScript runtime. */
  readonly token = signal<string | null>(null);
  /** Hold the mobile value needed by the OTP screen only in memory. */
  readonly pendingMobile = signal<string | null>(null);

  /** Construct the service with Angular's HTTP client. */
  constructor(private readonly http: HttpClient) {}

  /** Request an OTP for a mobile number.
   *
   * Args:
   *   mobileNumber: The ten-digit customer mobile number.
   * Returns: An observable that records the pending mobile after server validation.
   */
  requestOtp(mobileNumber: string): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${environment.apiBaseUrl}/api/auth/login`, { mobile_number: mobileNumber }).pipe(
      tap((response) => this.pendingMobile.set(response.mobile_number))
    );
  }

  /** Verify the fixed demo OTP and retain the issued token in memory.
   *
   * Args:
   *   otp: The OTP entered by the customer.
   * Returns: An observable that records the bearer token on success.
   */
  verifyOtp(otp: string): Observable<VerifyResponse> {
    const mobileNumber = this.pendingMobile();
    if (mobileNumber === null) {
      throw new Error('A mobile number is required before OTP verification.');
    }
    return this.http.post<VerifyResponse>(`${environment.apiBaseUrl}/api/auth/verify`, { mobile_number: mobileNumber, otp }).pipe(
      tap((response) => this.token.set(response.access_token))
    );
  }

  /** Clear every memory-only authentication value. */
  clearSession(): void {
    this.token.set(null);
    this.pendingMobile.set(null);
  }

  /** Determine whether a bearer token is present for a protected route.
   *
   * Returns: True when this page runtime has an authenticated session.
   */
  isAuthenticated(): boolean { return this.token() !== null; }
}
