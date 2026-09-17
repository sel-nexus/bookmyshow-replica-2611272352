/** Render the mobile number authentication form. */
import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { ReactiveFormsModule, FormControl, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';

import { AuthService } from '../../core/auth.service';

/** Collect and submit a valid mobile number before OTP verification. */
@Component({
  standalone: true,
  selector: 'app-login',
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  template: `<main class="page"><section class="panel" aria-labelledby="login-title"><p class="eyebrow">Secure entry</p><h1 id="login-title">Sign in.</h1><p>Use any ten-digit mobile number. You will verify it with the demo code on the next screen.</p><form (ngSubmit)="submit()" novalidate><label class="field" for="mobile">Mobile number<input id="mobile" type="tel" inputmode="numeric" autocomplete="tel" [formControl]="mobile" (input)="mobile.setValue($any($event.target).value)" aria-required="true" [attr.aria-invalid]="mobile.invalid && mobile.touched" aria-describedby="mobile-error" /></label><p id="mobile-error" class="error" role="alert" *ngIf="mobile.invalid && mobile.touched">Enter exactly ten digits.</p><p class="error" role="alert" *ngIf="error">{{ error }}</p><button class="button" type="button" [disabled]="submitting" (click)="submit()">{{ submitting ? 'Checking…' : 'Continue' }}</button></form><p class="status" aria-live="polite">{{ status }}</p><a routerLink="/">Back to home</a></section></main>`
})
export class LoginComponent {
  /** Hold the customer-entered mobile number. */
  readonly mobile = new FormControl('', { nonNullable: true, validators: [Validators.required, Validators.pattern(/^[0-9]{10}$/)] });
  /** Surface a safe request error. */
  error = '';
  /** Describe request progress to assistive technology. */
  status = '';
  /** Prevent duplicate request submission. */
  submitting = false;

  /** Construct the form with its dependencies. */
  constructor(private readonly auth: AuthService, private readonly router: Router) {}

  /** Submit a valid mobile request and navigate to OTP verification. */
  submit(): void {
    this.mobile.markAsTouched();
    if (this.mobile.invalid) { return; }
    this.submitting = true;
    this.status = 'Requesting your verification code.';
    this.error = '';
    this.auth.requestOtp(this.mobile.value).subscribe({
      next: () => void this.router.navigate(['/otp']),
      error: (response: HttpErrorResponse) => { this.error = response.error?.error?.message ?? 'We could not start verification.'; this.status = ''; this.submitting = false; },
      complete: () => { this.submitting = false; }
    });
  }
}
