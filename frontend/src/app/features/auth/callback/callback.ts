import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { firstValueFrom } from 'rxjs';

@Component({
    selector: 'app-callback',
    standalone: true,
    imports: [CommonModule, MatProgressSpinnerModule],
    templateUrl: './callback.html',
    styleUrls: ['./callback.scss']
})
export class CallbackComponent {
    private route = inject(ActivatedRoute);
    private authService = inject(AuthService);
    private router = inject(Router);

    isLoading = signal(true);
    error = signal('');

    constructor() {
        this.handleAuthCallback();
    }

    private async handleAuthCallback(): Promise<void> {
      const params = await firstValueFrom(this.route.queryParams);
      const code = params['code'];
      const state = params['state'];

      if (code && state) {
        try {
            await firstValueFrom(this.authService.handleCallback(code, state));
            await this.router.navigate(['/dashboard']);
        } catch (err) {
            console.error('Auth error:', err);
            this.error.set('Authentication failed. Please try again.');
            this.isLoading.set(false);
        }
      } else {
          this.error.set('Invalid callback parameters');
          this.isLoading.set(false);
      }
    }
}
