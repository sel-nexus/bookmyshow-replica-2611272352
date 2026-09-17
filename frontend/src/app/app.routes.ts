/** Define public, authentication, and protected client routes. */
import { Routes } from '@angular/router';

import { authGuard } from './core/auth.guard';
import { LandingComponent } from './features/auth/landing.component';
import { LoginComponent } from './features/auth/login.component';
import { OtpComponent } from './features/auth/otp.component';
import { CatalogueComponent } from './features/booking/catalogue.component';
import { SeatsComponent } from './features/booking/seats.component';
import { PaymentComponent } from './features/booking/payment.component';
import { ConfirmationComponent } from './features/booking/confirmation.component';
import { TheatresComponent } from './features/booking/theatres.component';

/** Export the application's navigable routes. */
export const routes: Routes = [
  { path: '', component: LandingComponent, title: 'BookMyShow' },
  { path: 'login', component: LoginComponent, title: 'Sign in | BookMyShow' },
  { path: 'otp', component: OtpComponent, title: 'Verify OTP | BookMyShow' },
  { path: 'movies', component: CatalogueComponent, canActivate: [authGuard], title: 'Movies | BookMyShow' },
  { path: 'theatres', component: TheatresComponent, canActivate: [authGuard], title: 'Theatres | BookMyShow' },
  { path: 'seats', component: SeatsComponent, canActivate: [authGuard], title: 'Seats | BookMyShow' },
  { path: 'payment', component: PaymentComponent, canActivate: [authGuard], title: 'Payment | BookMyShow' },
  { path: 'confirmation/:confirmationId', component: ConfirmationComponent, canActivate: [authGuard], title: 'Confirmation | BookMyShow' },
  { path: '**', redirectTo: '' }
];
