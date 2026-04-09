import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../services/api.service';

interface AssessmentItem {
  exams: string[];
  min_requirements: number;
}

interface AssessmentGroup {
  group_name: string;
  requirement_grouping: string;
  items: AssessmentItem[];
}

@Component({
  selector: 'app-assessment-detail',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './assessment-detail.component.html',
  styleUrl: './assessment-detail.component.scss',
})
export class AssessmentDetailComponent implements OnInit {
  assessmentId = '';
  assessment: any = null;
  activeTab: 'expert' | 'advanced' = 'expert';
  showPickerFor: { groupIdx: number; itemIdx: number } | null = null;
  examSearch = '';
  iLearnAssessments: any[] = [];
  filteredAssessments: any[] = [];

  constructor(private route: ActivatedRoute, private router: Router, private api: ApiService) {}

  ngOnInit() {
    this.assessmentId = this.route.snapshot.paramMap.get('id') || '';
    this.api.getILearnAssessments().subscribe(a => {
      this.iLearnAssessments = a;
      this.filteredAssessments = a;
    });
    if (this.assessmentId === 'new') {
      this.assessment = { name: '', competency_element: '', description: '', expert_groups: [], advanced_groups: [] };
    } else {
      this.api.getAssessment(this.assessmentId).subscribe({
        next: a => this.assessment = a,
        error: () => {
          this.assessment = { name: '', competency_element: '', description: '', expert_groups: [], advanced_groups: [] };
        }
      });
    }
  }

  get activeGroups(): AssessmentGroup[] {
    return this.activeTab === 'expert' ? this.assessment.expert_groups : this.assessment.advanced_groups;
  }

  get pageTitle(): string {
    if (!this.assessment) return '';
    const typeLabel = this.assessment.name === 'PLE' ? 'Proficiency Level Exam'
                    : this.assessment.name === 'CPA' ? 'Competency Performance Assessment'
                    : 'On-the-Job Training';
    return `${typeLabel} | ${this.assessment.competency_element}`;
  }

  addGroup() {
    this.activeGroups.push({ group_name: '', requirement_grouping: 'And', items: [{ exams: [], min_requirements: 1 }] });
  }

  removeGroup(i: number) { this.activeGroups.splice(i, 1); }

  removeItem(gi: number, ii: number) { this.activeGroups[gi].items.splice(ii, 1); }

  removeExam(gi: number, ii: number, exam: string) {
    const item = this.activeGroups[gi].items[ii];
    item.exams = item.exams.filter(e => e !== exam);
  }

  openPicker(gi: number, ii: number) {
    this.showPickerFor = { groupIdx: gi, itemIdx: ii };
    this.examSearch = '';
    this.filteredAssessments = this.iLearnAssessments;
  }

  onExamSearch() {
    const q = this.examSearch.toLowerCase();
    this.filteredAssessments = q
      ? this.iLearnAssessments.filter(a =>
          a.title.toLowerCase().includes(q) ||
          (a.cat_exam_name || '').toLowerCase().includes(q) ||
          (a.competency_element || '').toLowerCase().includes(q) ||
          (a.type || '').toLowerCase().includes(q)
        )
      : this.iLearnAssessments;
  }

  selectAssessment(a: any) {
    if (!this.showPickerFor) return;
    const { groupIdx, itemIdx } = this.showPickerFor;
    const item = this.activeGroups[groupIdx].items[itemIdx];
    const name = a.cat_exam_name || a.title.toUpperCase();
    if (!item.exams.includes(name)) item.exams.push(name);
    this.showPickerFor = null;
  }

  openILearnAssessment(catExamName: string) {
    this.api.lookupILearnAssessment(catExamName).subscribe({
      next: a => window.open(`http://localhost:4201/assessments/${a._id}`, '_blank'),
      error: () => window.open('http://localhost:4201/assessments', '_blank')
    });
  }

  minOptions(item: AssessmentItem): number[] {
    return Array.from({ length: Math.max(item.exams.length, 1) }, (_, i) => i + 1);
  }

  save() {
    const obs = this.assessmentId === 'new'
      ? this.api.createAssessment(this.assessment)
      : this.api.updateAssessment(this.assessmentId, this.assessment);
    obs.subscribe(() => this.router.navigate(['/content-management']));
  }

  cancel() { this.router.navigate(['/content-management']); }
}
