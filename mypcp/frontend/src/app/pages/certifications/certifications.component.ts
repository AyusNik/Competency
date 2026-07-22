import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { DashboardService } from '../../services/dashboard.service';

interface Certification {
  id: string;
  name: string;
  certification_type: 'ilearn' | 'xylem' | 'cbt';
  certification_category: string;
  validity_status: 'valid' | 'expired' | 'pending';
  expires_on: string;
  provider: string;
  description: string;
}

@Component({
  selector: 'app-certifications',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './certifications.component.html',
  styleUrl: './certifications.component.scss',
})
export class CertificationsComponent implements OnInit {
  loading = true;
  error = '';

  userName = '';
  jobTitle = 'Contractor';
  totalCertifications = 0;
  overallTrainingCoefficient = 0;

  summary: any = null;
  certifications: Certification[] = [];
  selected: Certification | null = null;

  search = '';
  selectedType = '';
  selectedValidity = '';

  constructor(private dashboardService: DashboardService, private router: Router) {}

  ngOnInit(): void {
    this.dashboardService.getMyCertifications().subscribe({
      next: (res) => {
        this.userName = res.user?.name || 'User';
        this.jobTitle = res.user?.job_title || 'Contractor';
        this.summary = res.summary;
        this.certifications = res.certifications || [];
        this.totalCertifications = res.total_certifications || 0;
        this.overallTrainingCoefficient = res.overall_training_coefficient || 0;
        this.loading = false;
      },
      error: () => {
        this.error = 'Failed to load certifications';
        this.loading = false;
      },
    });
  }

  goToDashboard() {
    this.router.navigate(['/dashboard']);
  }

  get filteredCertifications(): Certification[] {
    return this.certifications.filter((cert) => {
      const matchesName = !this.search || cert.name.toLowerCase().includes(this.search.toLowerCase());
      const matchesType = !this.selectedType || cert.certification_type === this.selectedType;
      const matchesValidity = !this.selectedValidity || cert.validity_status === this.selectedValidity;
      return matchesName && matchesType && matchesValidity;
    });
  }

  selectCertification(cert: Certification) {
    this.selected = cert;
  }

  clearFilters() {
    this.search = '';
    this.selectedType = '';
    this.selectedValidity = '';
  }

  statusDotClass(status: string): string {
    if (status === 'valid') return 'dot-valid';
    if (status === 'expired') return 'dot-expired';
    return 'dot-pending';
  }

  prettyStatus(status: string): string {
    return status.charAt(0).toUpperCase() + status.slice(1);
  }

  prettyType(type: string): string {
    if (type === 'ilearn') return 'iLearn';
    if (type === 'xylem') return 'Xylem';
    return 'CBT';
  }

  cardValue(card: 'summary' | 'generic' | 'function' | 'local' | 'learning'): string {
    if (!this.summary?.[card]) return '0 / 0';
    const c = this.summary[card];
    return `${c.done} / ${c.total}`;
  }

  cardPct(card: 'summary' | 'generic' | 'function' | 'local' | 'learning'): number {
    return this.summary?.[card]?.pct || 0;
  }
}
