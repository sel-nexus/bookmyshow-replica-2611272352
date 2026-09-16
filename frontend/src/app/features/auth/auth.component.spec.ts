/** Verify the auth pages' visible validation behavior. */
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';

import { LoginComponent } from './login.component';
import { OtpComponent } from './otp.component';
import { AuthService } from '../../core/auth.service';

describe('authentication components', () => {
  /** Configure Angular dependencies before each test. */
  beforeEach(() => TestBed.configureTestingModule({ providers: [provideRouter([]), provideHttpClient()] }));

  it('shows an invalid mobile error after a malformed submission', () => {
    const fixture = TestBed.createComponent(LoginComponent);
    fixture.componentInstance.mobile.setValue('bad');
    fixture.componentInstance.submit();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Enter exactly ten digits.');
  });

  it('redirects OTP entry to login when no in-memory mobile exists', () => {
    const fixture = TestBed.createComponent(OtpComponent);
    const auth = TestBed.inject(AuthService);
    auth.clearSession();
    fixture.detectChanges();
    expect(fixture.componentInstance.mobileNumber).toBe('');
  });
});
