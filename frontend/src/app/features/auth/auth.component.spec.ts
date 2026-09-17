import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';

import { AuthService } from '../../core/auth.service';
import { LoginComponent } from './login.component';
import { OtpComponent } from './otp.component';

describe('authentication components', () => {
  let http: HttpTestingController;
  let router: Router;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()] });
    http = TestBed.inject(HttpTestingController);
    router = TestBed.inject(Router);
  });

  afterEach(() => http.verify());

  it('shows an accessible invalid-mobile error without sending a request', () => {
    const fixture = TestBed.createComponent(LoginComponent);
    fixture.detectChanges();

    fixture.componentInstance.mobile.setValue('bad');
    fixture.componentInstance.submit();
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('[role="alert"]')?.textContent).toContain('Enter exactly ten digits.');
    http.expectNone('/api/auth/login');
  });

  it('uses the OTP response to navigate a valid mobile submission to the verification page', () => {
    const navigate = spyOn(router, 'navigate').and.resolveTo(true);
    const fixture = TestBed.createComponent(LoginComponent);
    fixture.componentInstance.mobile.setValue('9876543210');
    fixture.componentInstance.submit();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Checking…');
    http.expectOne('/api/auth/login').flush({ authentication_state: 'otp_required', mobile_number: '9876543210' });

    expect(navigate).toHaveBeenCalledWith(['/otp']);
    expect(TestBed.inject(AuthService).pendingMobile()).toBe('9876543210');
  });

  it('shows the backend mobile error in the accessible error region', () => {
    const fixture = TestBed.createComponent(LoginComponent);
    fixture.componentInstance.mobile.setValue('9876543210');
    fixture.componentInstance.submit();
    http.expectOne('/api/auth/login').flush({ error: { message: 'Mobile number is blocked.' } }, { status: 422, statusText: 'Invalid' });
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('[role="alert"]')?.textContent).toContain('Mobile number is blocked.');
  });

  it('redirects an OTP page without a pending mobile number to login', () => {
    const navigate = spyOn(router, 'navigate').and.resolveTo(true);
    const fixture = TestBed.createComponent(OtpComponent);

    fixture.detectChanges();

    expect(navigate).toHaveBeenCalledWith(['/login']);
  });

  it('verifies a valid OTP, stores the token, and navigates to films', () => {
    const auth = TestBed.inject(AuthService);
    auth.pendingMobile.set('9876543210');
    const navigate = spyOn(router, 'navigate').and.resolveTo(true);
    const fixture = TestBed.createComponent(OtpComponent);
    fixture.detectChanges();
    fixture.componentInstance.otp.setValue('1234');
    fixture.componentInstance.submit();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Verifying…');
    http.expectOne('/api/auth/verify').flush({ access_token: 'issued-token', token_type: 'bearer', expires_in: 1800, user: { id: 'user-id', mobile_number: '9876543210' } });

    expect(auth.token()).toBe('issued-token');
    expect(navigate).toHaveBeenCalledWith(['/movies']);
  });

  it('shows the backend OTP rejection in the accessible error region', () => {
    TestBed.inject(AuthService).pendingMobile.set('9876543210');
    const fixture = TestBed.createComponent(OtpComponent);
    fixture.detectChanges();
    fixture.componentInstance.otp.setValue('9999');
    fixture.componentInstance.submit();
    http.expectOne('/api/auth/verify').flush({ error: { message: 'The verification code is incorrect.' } }, { status: 401, statusText: 'Unauthorized' });
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('[role="alert"]')?.textContent).toContain('The verification code is incorrect.');
  });
});
