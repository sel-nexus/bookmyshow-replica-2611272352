/** Render and select the persisted movie catalogue. */
import { Component, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';

import { ApiService, Movie } from '../../core/api.service';
import { BookingStore } from './booking.store';

/** Display backend catalogue data and advance to theatre selection. */
@Component({
  standalone: true,
  selector: 'app-catalogue',
  template: `<main class="page booking-page"><section class="panel catalogue-panel"><p class="eyebrow">Step 1 of 3</p><h1>Choose a movie</h1><p class="status" aria-live="polite">{{ status() }}</p><div class="selection-grid">@for (movie of movies(); track movie.id) {<button class="selection-card" type="button" (click)="select(movie)" [attr.aria-label]="'Select ' + movie.title"><span class="poster-mark" aria-hidden="true">{{ movie.title.slice(0, 1) }}</span><strong>{{ movie.title }}</strong><small>{{ movie.poster_placeholder }}</small></button>}</div></section></main>`
})
export class CatalogueComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly store = inject(BookingStore);
  private readonly router = inject(Router);
  readonly movies = signal<Movie[]>([]);
  readonly status = signal('Loading available movies…');

  /** Load the authenticated catalogue once the route is active. */
  ngOnInit(): void {
    this.api.getMovies().subscribe({ next: (response) => { this.movies.set(response.movies); this.status.set('Select a movie to continue.'); }, error: () => this.status.set('Movies could not be loaded. Please try again.') });
  }

  /** Save the movie and navigate to its mapped theatre choices. */
  select(movie: Movie): void {
    this.store.selectMovie(movie);
    void this.router.navigate(['/theatres']);
  }
}
