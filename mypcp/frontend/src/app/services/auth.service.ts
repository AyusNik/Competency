import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { tap } from 'rxjs/operators';

const API = 'http://localhost:8001';

@Injectable({ providedIn: 'root' })
export class AuthService {
  constructor(private http: HttpClient, private router: Router) {}

  login(email: string, password: string) {
    return this.http.post<any>(`${API}/auth/login`, { email, password }).pipe(
      tap(res => {
        localStorage.setItem('token', res.access_token);
        localStorage.setItem('user_name', res.name);
        localStorage.setItem('job_title', res.job_title || '');
      })
    );
  }

  register(name: string, email: string, password: string, job_title: string) {
    return this.http.post<any>(`${API}/auth/register`, { name, email, password, job_title }).pipe(
      tap(res => {
        localStorage.setItem('token', res.access_token);
        localStorage.setItem('user_name', res.name);
        localStorage.setItem('job_title', res.job_title || '');
      })
    );
  }

  logout() {
    localStorage.clear();
    this.router.navigate(['/login']);
  }

  isLoggedIn(): boolean {
    return !!localStorage.getItem('token');
  }

  getToken(): string | null {
    return localStorage.getItem('token');
  }

  getUserName(): string {
    return localStorage.getItem('user_name') || '';
  }

  getJobTitle(): string {
    return localStorage.getItem('job_title') || '';
  }
}
