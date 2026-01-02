import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { firstValueFrom } from 'rxjs';

@Component({
    selector: 'app-login',
    standalone: true,
    imports: [CommonModule, MatButtonModule, MatCardModule, MatProgressSpinnerModule],
    templateUrl: './login.html',
    styleUrls: ['./login.scss']
})
export class LoginComponent {
    private authService = inject(AuthService);
    private router = inject(Router);

    loginUrl = signal('');
    isLoading = signal(false);

    constructor() {
        this.redirectIfAuthenticated();
    }

    private async redirectIfAuthenticated(): Promise<void> {
      const isAuth = await firstValueFrom(this.authService.isAuthenticated$);
      if (isAuth) {
            await this.router.navigate(['/dashboard']);
      }
    }

    async login(): Promise<void> {
        this.isLoading.set(true);
        try {
            const url = await firstValueFrom(this.authService.getLoginUrl());
            window.location.href = url;
        } catch (err) {
            console.error('Login URL fetch failed', err);
            this.isLoading.set(false);
        }
    }
}
