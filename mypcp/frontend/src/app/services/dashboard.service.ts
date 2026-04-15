import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

const API = 'http://localhost:8001';

@Injectable({ providedIn: 'root' })
export class DashboardService {
  constructor(private http: HttpClient) {}

  getMyDashboard() {
    return this.http.get<any>(`${API}/dashboard/me`);
  }

  getTrainingDetail(trainingId: string) {
    return this.http.get<any>(`${API}/dashboard/training/${trainingId}`);
  }

  toggleCourseComplete(courseId: string) {
    return this.http.post<any>(`${API}/progress/course/${courseId}/complete`, {});
  }

  toggleAssessmentComplete(assessmentId: string) {
    return this.http.post<any>(`${API}/progress/assessment/${assessmentId}/complete`, {});
  }
}
