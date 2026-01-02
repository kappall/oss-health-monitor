import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
    private apiUrl = environment.apiUrl;
    private tokenSubject = new BehaviorSubject<string | null>(this.getToken());
    public token$ = this.tokenSubject.asObservable();

    constructor(private http: HttpClient) {}

    getToken(): string | null {
        return localStorage.getItem('access_token');
    }

    setToken(token: string): void {
        localStorage.setItem('access_token', token);
        this.tokenSubject.next(token);
    }

    clearToken(): void {
        localStorage.removeItem('access_token');
        this.tokenSubject.next(null);
    }

    private getHeaders(): HttpHeaders {
        const token = this.getToken();
        if (token) {
        return new HttpHeaders({
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        });
        }
        return new HttpHeaders({
        'Content-Type': 'application/json'
        });
    }

    // Auth endpoints
    getLoginUrl(): Observable<any> {
        return this.http.get(`${this.apiUrl}/api/auth/login`);
    }

    getCurrentUser(): Observable<any> {
        return this.http.get(`${this.apiUrl}/api/auth/me`, {
        headers: this.getHeaders()
        });
    }

    // Project endpoints
    submitProject(repositoryUrl: string): Observable<any> {
        return this.http.post(`${this.apiUrl}/api/projects/submit`, {
        repository_url: repositoryUrl
        }, {
        headers: this.getHeaders()
        });
    }

    getProjects(page: number = 1, pageSize: number = 20): Observable<any> {
        return this.http.get(`${this.apiUrl}/api/projects/`, {
        params: { page, page_size: pageSize },
        headers: this.getHeaders()
        });
    }

    getProject(id: number): Observable<any> {
        return this.http.get(`${this.apiUrl}/api/projects/${id}`, {
        headers: this.getHeaders()
        });
    }

    deleteProject(id: number): Observable<void> {
        return this.http.delete<void>(`${this.apiUrl}/api/projects/${id}`, {
        headers: this.getHeaders()
        });
    }

    // Analysis endpoints
    analyzeProject(projectId: number): Observable<any> {
        return this.http.post(`${this.apiUrl}/api/analysis/analyze/${projectId}`, {}, {
        headers: this.getHeaders()
        });
    }

    getAnalysisExplanation(projectId: number): Observable<any> {
        return this.http.get(`${this.apiUrl}/api/analysis/explain/${projectId}`, {
        headers: this.getHeaders()
        });
    }

    // Dashboard endpoints
    getDashboardSummary(): Observable<any> {
        return this.http.get(`${this.apiUrl}/api/dashboard/summary`, {
        headers: this.getHeaders()
        });
    }

    getProjectTimeline(projectId: number): Observable<any> {
        return this.http.get(`${this.apiUrl}/api/dashboard/timeline/${projectId}`, {
        headers: this.getHeaders()
        });
    }

    getVulnerabilitiesSummary(): Observable<any> {
        return this.http.get(`${this.apiUrl}/api/dashboard/vulnerabilities`, {
        headers: this.getHeaders()
        });
    }

    // Favorites endpoints
    addFavorite(projectId: number): Observable<any> {
        return this.http.post(`${this.apiUrl}/api/favorites/`, {
        project_id: projectId
        }, {
        headers: this.getHeaders()
        });
    }

    removeFavorite(projectId: number): Observable<void> {
        return this.http.delete<void>(`${this.apiUrl}/api/favorites/${projectId}`, {
        headers: this.getHeaders()
        });
    }

    getFavorites(): Observable<any> {
        return this.http.get(`${this.apiUrl}/api/favorites/`, {
        headers: this.getHeaders()
        });
    }

    checkFavorite(projectId: number): Observable<any> {
        return this.http.get(`${this.apiUrl}/api/favorites/check/${projectId}`, {
        headers: this.getHeaders()
        });
    }
}
