/** Render the public cinematic entry page. */
import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

/** Present the public entry point and clear call to action. */
@Component({
  standalone: true,
  selector: 'app-landing',
  imports: [RouterLink],
  template: `<main class="page"><section class="panel" aria-labelledby="landing-title"><p class="eyebrow">The big screen awaits</p><h1 id="landing-title">Your next show starts here.</h1><p>Pick your film, reserve your favourite seats and feel the opening credits before you arrive.</p><a class="button" routerLink="/login">Enter the theatre</a></section></main>`
})
export class LandingComponent {}
