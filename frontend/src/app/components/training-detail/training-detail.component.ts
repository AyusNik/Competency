import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../services/api.service';

interface RequirementItem {
  courses: string[];
  min_requirements: number;
}

interface TrainingGroup {
  group_name: string;
  requirement_grouping: string;
  items: RequirementItem[];
}

@Component({
  selector: 'app-training-detail',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './training-detail.component.html',
  styleUrl: './training-detail.component.scss',
})
export class TrainingDetailComponent implements OnInit {
  trainingId = '';
  training: any = null;
  activeTab: 'basic' | 'advanced' = 'basic';
  showCoursePickerFor: { groupIdx: number; itemIdx: number } | null = null;
  courseSearch = '';
  iLearnCourses: any[] = [];
  filteredCourses: any[] = [];

  constructor(private route: ActivatedRoute, private router: Router, private api: ApiService) {}

  ngOnInit() {
    this.trainingId = this.route.snapshot.paramMap.get('id') || '';
    this.api.getILearnCourses().subscribe(c => {
      this.iLearnCourses = c;
      this.filteredCourses = c;
    });
    if (this.trainingId === 'new') {
      this.training = { name: '', description: '', basic_groups: [], advanced_groups: [] };
    } else {
      this.api.getTraining(this.trainingId).subscribe({
        next: t => this.training = t,
        error: () => {
          this.training = { name: '', description: '', basic_groups: [], advanced_groups: [] };
        }
      });
    }
  }

  get activeGroups(): TrainingGroup[] {
    return this.activeTab === 'basic' ? this.training.basic_groups : this.training.advanced_groups;
  }

  addGroup() {
    this.activeGroups.push({ group_name: '', requirement_grouping: 'And', items: [{ courses: [], min_requirements: 1 }] });
  }

  removeGroup(i: number) { this.activeGroups.splice(i, 1); }

  removeItem(groupIdx: number, itemIdx: number) {
    this.activeGroups[groupIdx].items.splice(itemIdx, 1);
  }

  removeCourse(groupIdx: number, itemIdx: number, course: string) {
    const item = this.activeGroups[groupIdx].items[itemIdx];
    item.courses = item.courses.filter(c => c !== course);
  }

  openCoursePicker(groupIdx: number, itemIdx: number) {
    this.showCoursePickerFor = { groupIdx, itemIdx };
    this.courseSearch = '';
    this.filteredCourses = this.iLearnCourses;
  }

  onCourseSearch() {
    const q = this.courseSearch.toLowerCase();
    this.filteredCourses = q
      ? this.iLearnCourses.filter(c =>
          c.title.toLowerCase().includes(q) ||
          (c.cat_course_name || '').toLowerCase().includes(q) ||
          (c.category || '').toLowerCase().includes(q)
        )
      : this.iLearnCourses;
  }

  selectCourse(course: any) {
    if (!this.showCoursePickerFor) return;
    const { groupIdx, itemIdx } = this.showCoursePickerFor;
    const item = this.activeGroups[groupIdx].items[itemIdx];
    const name = course.cat_course_name || course.title.toUpperCase();
    if (!item.courses.includes(name)) item.courses.push(name);
    this.showCoursePickerFor = null;
  }

  openILearnCourse(catCourseName: string) {
    this.api.lookupILearnCourse(catCourseName).subscribe({
      next: c => window.open(`http://localhost:4201/courses/${c._id}`, '_blank'),
      error: () => window.open('http://localhost:4201/courses', '_blank')
    });
  }

  minOptions(item: RequirementItem): number[] {
    return Array.from({ length: Math.max(item.courses.length, 1) }, (_, i) => i + 1);
  }

  save() {
    const obs = this.trainingId === 'new'
      ? this.api.createTraining(this.training)
      : this.api.updateTraining(this.trainingId, this.training);
    obs.subscribe(() => this.router.navigate(['/content-management']));
  }

  cancel() { this.router.navigate(['/content-management']); }
}
