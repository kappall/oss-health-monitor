import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { ApiService } from '../services/api.service';
import { AuthService } from '../services/auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
    const apiService = inject(ApiService);
    const authService = inject(AuthService);

    const token = apiService.getToken();

    const authReq = token
        ? req.clone({
            setHeaders: {
            Authorization: `Bearer ${token}`
            }
        })
        : req;

    return next(authReq).pipe(
        catchError(err => {
        if (err.status === 401 || err.status === 403) {
            authService.logout();
        }

        return throwError(() => err);
        })
    );
};
