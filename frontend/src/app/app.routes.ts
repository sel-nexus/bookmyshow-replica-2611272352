/** Define public, authentication, and protected client routes. */
import { Routes } from '@angular/router';

import { authGuard } from './core/auth.guard';
import { LandingComponent } from './features/auth/landing.component';
import { LoginComponent } from './features/auth/login.component';
import { OtpComponent } from './features/auth/otp.component';
import { MoviesComponent } from './movies.component';

/** Export the application's navigable routes. */
export const routes: Routes = [
  { path: '', component: LandingComponent, title: 'BookMyShow' },
  { path: 'login', component: LoginComponent, title: 'Sign in | BookMyShow' },
  { path: 'otp', component: OtpComponent, title: 'Verify OTP | BookMyShow' },
  { path: 'movies', component: MoviesComponent, canActivate: [authGuard], title: 'Movies | BookMyShow' },
  { path: '**', redirectTo: '' }
];
