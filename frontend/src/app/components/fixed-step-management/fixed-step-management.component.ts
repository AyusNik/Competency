import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-fixed-step-management',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './fixed-step-management.component.html',
  styleUrl: './fixed-step-management.component.scss',
})
export class FixedStepManagementComponent implements OnInit {
  competencies: any[] = [];
  editingId: string | null = null;
  editForm: any = {};
  saving = false;

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.api.getCompetencies().subscribe(c => this.competencies = c);
  }

  startEdit(comp: any) {
    this.editingId = comp._id;
    this.editForm = {
      name: comp.name,
      description: comp.description || '',
      promotion_from: comp.promotion_from || '',
      promotion_to: comp.promotion_to || '',
      order: comp.order ?? 0,
    };
  }

  cancelEdit() {
    this.editingId = null;
    this.editForm = {};
  }

  save(comp: any) {
    this.saving = true;
    this.api.updateCompetency(comp._id, this.editForm).subscribe({
      next: () => {
        Object.assign(comp, this.editForm);
        this.editingId = null;
        this.saving = false;
      },
      error: () => this.saving = false,
    });
  }
}

