import { Component, OnInit, ElementRef, ViewChild, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MinPipe } from '../../pipes/min.pipe';
import { ChatbotComponent } from '../../components/chatbot/chatbot.component';
import { Router } from '@angular/router';
import { DashboardService } from '../../services/dashboard.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, MinPipe, ChatbotComponent],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent implements OnInit, AfterViewInit {
  @ViewChild('donutCanvas') donutCanvas!: ElementRef<HTMLCanvasElement>;

  data: any = null;
  loading = true;
  error = '';
  search = '';
  page = 1;
  pageSize = 10;

  constructor(
    private dashSvc: DashboardService,
    private auth: AuthService,
    private router: Router
  ) {}

  ngOnInit() {
    this.dashSvc.getMyDashboard().subscribe({
      next: (d) => { this.data = d; this.loading = false; this.drawDonut(); },
      error: () => { this.error = 'Failed to load dashboard'; this.loading = false; },
    });
  }

  ngAfterViewInit() {
    if (this.data) this.drawDonut();
  }

  get filteredUnits() {
    if (!this.data?.units) return [];
    const q = this.search.toLowerCase();
    return this.data.units.filter((u: any) =>
      !q || u.unit_name.toLowerCase().includes(q)
    );
  }

  get pagedUnits() {
    const start = (this.page - 1) * this.pageSize;
    return this.filteredUnits.slice(start, start + this.pageSize);
  }

  get totalPages() {
    return Math.ceil(this.filteredUnits.length / this.pageSize);
  }

  clearSearch() { this.search = ''; this.page = 1; }

  drawDonut() {
    setTimeout(() => {
      const canvas = this.donutCanvas?.nativeElement;
      if (!canvas || !this.data) return;
      const ctx = canvas.getContext('2d')!;
      const lc = this.data.level_counts || { B: 0, I: 0, A: 0, E: 0 };
      const total = Object.values(lc).reduce((a: any, b: any) => a + b, 0) || 1;
      const segments = [
        { value: lc.B, color: '#93c5fd' },
        { value: lc.I, color: '#60a5fa' },
        { value: lc.A, color: '#2563eb' },
        { value: lc.E, color: '#1e3a8a' },
      ];
      const cx = canvas.width / 2, cy = canvas.height / 2, r = 70, inner = 44;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      let angle = -Math.PI / 2;
      for (const seg of segments) {
        const sweep = (seg.value / (total as number)) * 2 * Math.PI;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.arc(cx, cy, r, angle, angle + sweep);
        ctx.closePath();
        ctx.fillStyle = seg.color;
        ctx.fill();
        angle += sweep;
      }
      // Donut hole
      ctx.beginPath();
      ctx.arc(cx, cy, inner, 0, 2 * Math.PI);
      ctx.fillStyle = '#fff';
      ctx.fill();
      // Center text
      ctx.fillStyle = '#1a1a2e';
      ctx.font = 'bold 22px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(String(this.data.total_elements), cx, cy - 6);
      ctx.font = '11px Inter, sans-serif';
      ctx.fillStyle = '#6b7280';
      ctx.fillText('elements', cx, cy + 12);
    }, 50);
  }

  openILearn(item: any, type: 'course' | 'assessment') {
    const base = 'http://localhost:4201';
    const path = type === 'course' ? 'courses' : 'assessments';
    window.open(`${base}/${path}/${item._id}`, '_blank');
  }

  toggleComplete(courseId: string, unit: any) {
    if (this.isCompleted(courseId, unit)) return;
    this.dashSvc.toggleCourseComplete(courseId).subscribe({
      next: () => {
        unit.completed_course_ids = [...(unit.completed_course_ids || []), courseId];
        this.refreshUnitState(unit);
      },
    });
  }

  isPleAccessible(assessment: any): boolean {
    if (!this.isPle(assessment)) return true;
    return assessment.ple_accessible === true;
  }

  toggleAssessmentComplete(assessmentId: string, unit: any, assessment: any) {
    if (this.isAssessmentCompleted(assessmentId, unit)) return;
    if (this.isPle(assessment) && !this.isPleAccessible(assessment)) return;
    this.dashSvc.toggleAssessmentComplete(assessmentId).subscribe({
      next: () => {
        unit.completed_assessment_ids = [...(unit.completed_assessment_ids || []), assessmentId];
        this.refreshUnitState(unit);
        this.refreshOdyssey();
      },
    });
  }

  private refreshUnitState(unit: any) {
    const allCourseIds = unit.ilearn_courses.map((c: any) => c._id);
    const allAssessmentIds = unit.ilearn_assessments.map((a: any) => a._id);
    const coursesDone = allCourseIds.length > 0 && allCourseIds.every((id: string) => unit.completed_course_ids.includes(id));
    const assessmentsDone = allAssessmentIds.length > 0 && allAssessmentIds.every((id: string) => unit.completed_assessment_ids.includes(id));
    const dateLocked = unit.release_info?.length > 0;
    unit.assessments_unlocked = !dateLocked;
    unit.cpa_unlocked = coursesDone && !dateLocked;
    unit.element_complete = coursesDone && assessmentsDone;
  }

  private refreshOdyssey() {
    if (!this.data?.odyssey || !this.data?.units) return;
    let prevComplete = true;
    for (const o of this.data.odyssey) {
      const compUnits = this.data.units.filter((u: any) => u.competency === o.competency);
      o.elements_done = compUnits.filter((u: any) => u.element_complete).length;
      o.elements_total = compUnits.length;
      o.progress_pct = o.elements_total ? Math.round((o.elements_done / o.elements_total) * 100) : 0;
      o.is_complete = o.progress_pct === 100;
      o.locked = !prevComplete;
      prevComplete = o.is_complete;
    }
    // Update current_position
    const lastComplete = [...this.data.odyssey].reverse().find((o: any) => o.is_complete);
    if (lastComplete?.promotion_to) this.data.current_position = lastComplete.promotion_to;
  }

  private expandedTrainings = new Set<string>();

  toggleTraining(key: string) {
    this.expandedTrainings.has(key) ? this.expandedTrainings.delete(key) : this.expandedTrainings.add(key);
  }

  isTrainingExpanded(key: string): boolean {
    return this.expandedTrainings.has(key);
  }

  openTraining(trainingId: string) {
    this.router.navigate(['/training', trainingId]);
  }

  get hasOdysseyTiers(): boolean {
    return (this.data?.odyssey || []).some((o: any) => o.promotion_from && o.promotion_to);
  }

  isTrainingComplete(training: any, unit: any): boolean {
    return training.courses.length > 0 && training.courses.every((c: any) => this.isCompleted(c._id, unit));
  }

  toggleTrainingComplete(training: any, unit: any) {
    const allDone = this.isTrainingComplete(training, unit);
    training.courses.forEach((c: any) => {
      const done = this.isCompleted(c._id, unit);
      if (!allDone && !done) this.toggleComplete(c._id, unit);
      else if (allDone && done) this.toggleComplete(c._id, unit);
    });
  }

  isAssessmentUnlocked(assessment: any, unit: any): boolean {
    const isCPA = (assessment.type || '').toUpperCase() === 'CPA';
    return isCPA ? unit.cpa_unlocked : unit.assessments_unlocked;
  }

  isCompleted(courseId: string, unit: any): boolean {
    return (unit.completed_course_ids || []).includes(courseId);
  }

  isAssessmentCompleted(assessmentId: string, unit: any): boolean {
    return (unit.completed_assessment_ids || []).includes(assessmentId);
  }

  plePopup: { assessment: any; unit: any } | null = null;

  openPlePopup(assessment: any, unit: any) {
    if (this.isAssessmentCompleted(assessment._id, unit)) return;
    this.plePopup = { assessment, unit };
  }

  closePlePopup() { this.plePopup = null; }

  openPleILearn() {
    if (!this.plePopup) return;
    this.openILearn(this.plePopup.assessment, 'assessment');
    this.closePlePopup();
  }

  openUnmappedPleILearn() {
    if (!this.plePopup) return;
    const examName = this.plePopup.assessment.cat_exam_name || this.plePopup.assessment.title;
    this.closePlePopup();
    this.router.navigate(['/ple-detail'], { queryParams: { exam: examName } });
  }

  isPle(assessment: any): boolean {
    return (assessment.type || '').toUpperCase() === 'PLE';
  }

  logout() { this.auth.logout(); }
}
