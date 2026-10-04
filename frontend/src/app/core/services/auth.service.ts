import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { map, catchError, tap } from 'rxjs/operators';
import { ApiService } from './api.service';
import { environment } from '../../../environments/environment';

interface AuthCallbackResponse {
    access_token: string;
}

@Injectable({
    providedIn: 'root'
})
export class AuthService {
    private currentUserSubject = new BehaviorSubject<any>(null);
    public currentUser$ = this.currentUserSubject.asObservable();

    private isAuthenticatedSubject = new BehaviorSubject<boolean>(this.hasToken());
    public isAuthenticated$ = this.isAuthenticatedSubject.asObservable();

    constructor(
        private http: HttpClient,
        private apiService: ApiService
    ) {
        this.loadUser();
    }

    private hasToken(): boolean {
        return !!localStorage.getItem('access_token');
    }

    private loadUser(): void {
        if (this.hasToken()) {
        this.apiService.getCurrentUser().pipe(
            tap(user => {
            this.currentUserSubject.next(user);
            this.isAuthenticatedSubject.next(true);
            }),
                catchError(() => {
            this.logout();
            return of(null);
            })
        ).subscribe();
        }
    }

    getLoginUrl(): Observable<string> {
        return this.apiService.getLoginUrl().pipe(
        map(response => response.authorization_url)
        );
    }



    handleCallback(code: string, state: string): Observable<AuthCallbackResponse> {
    return this.http.get<AuthCallbackResponse>(
        `${environment.apiUrl}/api/auth/callback`,
        { params: { code, state } }
    ).pipe(
        tap(response => {
        this.apiService.setToken(response.access_token);
        this.isAuthenticatedSubject.next(true);
        this.loadUser();
        })
    );
    }


    getCurrentUser(): Observable<any> {
        return this.currentUser$;
    }

    isAuthenticated(): Observable<boolean> {
        return this.isAuthenticated$;
    }

    logout(): void {
        this.apiService.clearToken();
        this.currentUserSubject.next(null);
        this.isAuthenticatedSubject.next(false);
    }
}
