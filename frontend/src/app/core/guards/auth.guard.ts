import { CanActivateFn, Router, UrlTree } from '@angular/router';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';
import { take, map } from 'rxjs';

export const authGuard: CanActivateFn = (route, state) => {
    const authService = inject(AuthService);
    const router = inject(Router);

    const isAuthenticated = authService.isAuthenticated$;

    return isAuthenticated.pipe(
        take(1),
        map(isAuth => {
        if (isAuth) {
            return true;
        }
        return router.parseUrl('/login');
        })
    );
};
