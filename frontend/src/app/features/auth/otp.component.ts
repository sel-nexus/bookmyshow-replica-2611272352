/** Render the fixed OTP verification form. */
import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { ReactiveFormsModule, FormControl, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';

import { AuthService } from '../../core/auth.service';

/** Verify the demo OTP and enter the protected experience. */
@Component({
  standalone: true,
  selector: 'app-otp',
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  template: `<main class="page"><section class="panel" aria-labelledby="otp-title"><p class="eyebrow">One last frame</p><h1 id="otp-title">Verify code.</h1><p>We sent a demo code for {{ mobileNumber }}. For this demo, use <strong>1234</strong>.</p><form (ngSubmit)="submit()" novalidate><label class="field" for="otp">One-time password<input id="otp" type="text" inputmode="numeric" autocomplete="one-time-code" [formControl]="otp" (input)="otp.setValue($any($event.target).value)" aria-required="true" [attr.aria-invalid]="otp.invalid && otp.touched" aria-describedby="otp-error" /></label><p id="otp-error" class="error" role="alert" *ngIf="otp.invalid && otp.touched">Enter the four-digit demo code.</p><p class="error" role="alert" *ngIf="error">{{ error }}</p><button class="button" type="button" [disabled]="submitting" (click)="submit()">{{ submitting ? 'Verifying…' : 'Reveal films' }}</button></form><p class="status" aria-live="polite">{{ status }}</p><a routerLink="/login">Use another number</a></section></main>`
})
export class OtpComponent implements OnInit {
  /** Hold the OTP input. */
  readonly otp = new FormControl('', { nonNullable: true, validators: [Validators.required, Validators.pattern(/^[0-9]{4}$/)] });
  /** Render the pending mobile without persistent storage. */
  mobileNumber = '';
  /** Surface a safe verification error. */
  error = '';
  /** Announce verification progress. */
  status = '';
  /** Prevent duplicate OTP submissions. */
  submitting = false;

  /** Construct the page with auth and navigation dependencies. */
  constructor(private readonly auth: AuthService, private readonly router: Router) {}

  /** Redirect when no mobile request exists in this runtime. */
  ngOnInit(): void {
    const pending = this.auth.pendingMobile();
    if (pending === null) { void this.router.navigate(['/login']); return; }
    this.mobileNumber = pending;
  }

  /** Submit a valid OTP and enter protected movies. */
  submit(): void {
    this.otp.markAsTouched();
    if (this.otp.invalid) { return; }
    this.submitting = true;
    this.status = 'Verifying your code.';
    this.error = '';
    this.auth.verifyOtp(this.otp.value).subscribe({
      next: () => void this.router.navigate(['/movies']),
      error: (response: HttpErrorResponse) => { this.error = response.error?.error?.message ?? 'We could not verify that code.'; this.status = ''; this.submitting = false; },
      complete: () => { this.submitting = false; }
    });
  }
}
