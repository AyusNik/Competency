import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { debounceTime, distinctUntilChanged, Subject } from 'rxjs';

@Component({
  selector: 'app-content-management',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './content-management.component.html',
  styleUrl: './content-management.component.scss',
})
export class ContentManagementComponent implements OnInit {
  mappings: any[] = [];
  trainings: any[] = [];
  allAssessments: any[] = [];
  searchTerm = '';
  showModal = false;
  editingId: string | null = null;
  private search$ = new Subject<string>();

  form = {
    ce_unit: '',
    competency_element: '',
    plr_table: '',
    training_ids: [] as string[],
    assessment_ids: [] as string[],
    assessment_types: [] as string[],
  };

  assessmentOptions = ['PLE', 'CPA', 'OJT']; // kept for reference

  constructor(private api: ApiService, private router: Router) {}

  ngOnInit() {
    this.load();
    this.api.getTrainings().subscribe(t => this.trainings = t);
    this.api.getAssessments().subscribe(a => this.allAssessments = a);
    this.search$.pipe(debounceTime(300), distinctUntilChanged()).subscribe((v) => this.load(v));
  }

  load(search?: string) {
    this.api.getContentMappings(search).subscribe((data) => (this.mappings = data));
  }

  onSearch() {
    this.search$.next(this.searchTerm);
  }

  openAdd() {
    this.editingId = null;
    this.form = { ce_unit: '', competency_element: '', plr_table: '', training_ids: [], assessment_ids: [], assessment_types: [] };
    this.showModal = true;
  }

  openEdit(m: any) {
    this.editingId = m._id;
    this.form = { ce_unit: m.ce_unit, competency_element: m.competency_element, plr_table: m.plr_table, training_ids: [...m.training_ids], assessment_ids: [...(m.assessment_ids||[])], assessment_types: [...m.assessment_types] };
    this.showModal = true;
  }

  save() {
    const obs = this.editingId
      ? this.api.updateContentMapping(this.editingId, this.form)
      : this.api.createContentMapping(this.form);
    obs.subscribe(() => { this.showModal = false; this.load(this.searchTerm); });
  }

  delete(id: string) {
    if (confirm('Delete this record?')) {
      this.api.deleteContentMapping(id).subscribe(() => this.load(this.searchTerm));
    }
  }

  openTraining(trainingId: string) {
    this.router.navigate(['/training', trainingId]);
  }

  openAssessment(assessmentId: string) {
    this.router.navigate(['/assessment', assessmentId]);
  }

  newTraining() {
    this.router.navigate(['/training', 'new']);
  }

  trainingName(id: string): string {
    return this.trainings.find(t => t._id === id)?.name || id;
  }

  toggleTraining(id: string) {
    const idx = this.form.training_ids.indexOf(id);
    idx === -1 ? this.form.training_ids.push(id) : this.form.training_ids.splice(idx, 1);
  }

  onTrainingIdsChange(value: string) {
    this.form.training_ids = value.split(',').map(s => s.trim()).filter(Boolean);
  }

  toggleAssessment(id: string, type: string) {
    const idx = this.form.assessment_ids.indexOf(id);
    if (idx === -1) {
      this.form.assessment_ids.push(id);
      this.form.assessment_types.push(type);
    } else {
      this.form.assessment_ids.splice(idx, 1);
      this.form.assessment_types.splice(idx, 1);
    }
  }
}
