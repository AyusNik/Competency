import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

const BASE = 'http://localhost:8005';

@Injectable({ providedIn: 'root' })
export class ApiService {
  constructor(private http: HttpClient) {}

  getContentMappings(search?: string): Observable<any[]> {
    let params = new HttpParams();
    if (search) params = params.set('search', search);
    return this.http.get<any[]>(`${BASE}/content-mappings`, { params });
  }

  createContentMapping(data: any): Observable<any> {
    return this.http.post(`${BASE}/content-mappings`, data);
  }

  updateContentMapping(id: string, data: any): Observable<any> {
    return this.http.put(`${BASE}/content-mappings/${id}`, data);
  }

  deleteContentMapping(id: string): Observable<any> {
    return this.http.delete(`${BASE}/content-mappings/${id}`);
  }

  getCompetencies(): Observable<any[]> {
    return this.http.get<any[]>(`${BASE}/competencies`);
  }

  updateCompetency(id: string, data: any): Observable<any> {
    return this.http.put(`${BASE}/competencies/${id}`, data);
  }

  getTrainings(): Observable<any[]> {
    return this.http.get<any[]>(`${BASE}/trainings`);
  }

  getTraining(id: string): Observable<any> {
    return this.http.get<any>(`${BASE}/trainings/${id}`);
  }

  createTraining(data: any): Observable<any> {
    return this.http.post(`${BASE}/trainings`, data);
  }

  updateTraining(id: string, data: any): Observable<any> {
    return this.http.put(`${BASE}/trainings/${id}`, data);
  }

  deleteTraining(id: string): Observable<any> {
    return this.http.delete(`${BASE}/trainings/${id}`);
  }

  getCourses(): Observable<any[]> {
    return this.http.get<any[]>(`${BASE}/courses`);
  }

  getPlr(): Observable<any[]> {
    return this.http.get<any[]>(`${BASE}/plr`);
  }

  getAssessments(): Observable<any[]> {
    return this.http.get<any[]>(`${BASE}/assessments`);
  }

  getAssessment(id: string): Observable<any> {
    return this.http.get<any>(`${BASE}/assessments/${id}`);
  }

  createAssessment(data: any): Observable<any> {
    return this.http.post(`${BASE}/assessments`, data);
  }

  updateAssessment(id: string, data: any): Observable<any> {
    return this.http.put(`${BASE}/assessments/${id}`, data);
  }

  deleteAssessment(id: string): Observable<any> {
    return this.http.delete(`${BASE}/assessments/${id}`);
  }

  // ILearn integration
  getILearnCourses(): Observable<any[]> {
    return this.http.get<any[]>(`${BASE}/ilearn/courses`);
  }

  getILearnAssessments(): Observable<any[]> {
    return this.http.get<any[]>(`${BASE}/ilearn/assessments`);
  }

  lookupILearnCourse(catCourseName: string): Observable<any> {
    return this.http.get<any>(`${BASE}/ilearn/lookup/course`, { params: { name: catCourseName } });
  }

  lookupILearnAssessment(catExamName: string): Observable<any> {
    return this.http.get<any>(`${BASE}/ilearn/lookup/assessment`, { params: { name: catExamName } });
  }
}
