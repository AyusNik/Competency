import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

const BASE = 'http://localhost:8005/ilearn';

@Injectable({ providedIn: 'root' })
export class IlearnService {
  constructor(private http: HttpClient) {}

  getCourses(search?: string, category?: string): Observable<any[]> {
    let params = new HttpParams();
    if (search) params = params.set('search', search);
    if (category && category !== 'All') params = params.set('category', category);
    return this.http.get<any[]>(`${BASE}/courses`, { params });
  }

  getCourse(id: string): Observable<any> {
    return this.http.get<any>(`${BASE}/courses/${id}`);
  }

  getAssessments(search?: string, category?: string, type?: string): Observable<any[]> {
    let params = new HttpParams();
    if (search) params = params.set('search', search);
    if (category && category !== 'All') params = params.set('category', category);
    if (type && type !== 'All') params = params.set('type', type);
    return this.http.get<any[]>(`${BASE}/assessments`, { params });
  }

  getAssessment(id: string): Observable<any> {
    return this.http.get<any>(`${BASE}/assessments/${id}`);
  }

  getCategories(): Observable<string[]> {
    return this.http.get<string[]>(`${BASE}/categories`);
  }

  getStats(): Observable<any> {
    return this.http.get<any>(`${BASE}/stats`);
  }
}
