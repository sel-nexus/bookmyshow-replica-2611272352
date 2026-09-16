/** Render the minimal authenticated destination for this slice. */
import { Component } from '@angular/core';

/** Present a complete protected route landing state. */
@Component({
  standalone: true,
  selector: 'app-movies',
  template: `<main class="page"><section class="panel"><p class="eyebrow">You are in</p><h1>Films arriving next.</h1><p>Your secure entry is confirmed. The movie catalogue follows in the next feature slice.</p></section></main>`
})
export class MoviesComponent {}
