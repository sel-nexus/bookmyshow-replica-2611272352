/** Bootstrap the standalone BookMyShow client. */
import { Component } from '@angular/core';
import { bootstrapApplication } from '@angular/platform-browser';
import { RouterOutlet } from '@angular/router';

import { appConfig } from './app/app.config';

/** Host routed feature pages. */
@Component({ standalone: true, selector: 'app-root', imports: [RouterOutlet], template: '<router-outlet />' })
class AppComponent {}

/** Start the Angular application. */
bootstrapApplication(AppComponent, appConfig).catch((error: unknown) => console.error('Application bootstrap failed', error));
