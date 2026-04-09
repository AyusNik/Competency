import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { IlearnService } from '../../services/ilearn.service';
import { TrustUrlPipe } from '../../pipes/trust-url.pipe';

@Component({
  selector: 'app-course-detail',
  standalone: true,
  imports: [CommonModule, RouterLink, TrustUrlPipe],
  templateUrl: './course-detail.component.html',
  styleUrl: './course-detail.component.scss'
})
export class CourseDetailComponent implements OnInit {
  course: any = null;
  loading = true;
  error = '';
  contentUnavailable = false;

  constructor(private route: ActivatedRoute, private svc: IlearnService) {}

  ngOnInit() {
    const id = this.route.snapshot.paramMap.get('id')!;
    this.svc.getCourse(id).subscribe({
      next: c => { this.course = c; this.loading = false; },
      error: () => { this.error = 'Course not found.'; this.loading = false; }
    });
  }

  onIframeLoad(event: Event) {
    const iframe = event.target as HTMLIFrameElement;
    try {
      // If iframe loaded but has no content (blocked/unavailable), contentDocument will be empty or inaccessible
      const doc = iframe.contentDocument || iframe.contentWindow?.document;
      if (!doc || doc.body?.innerHTML === '') {
        this.contentUnavailable = true;
      }
    } catch {
      // Cross-origin block means YouTube loaded fine — not unavailable
    }
    // Also check after a short delay for YouTube's "Video unavailable" state
    setTimeout(() => {
      try {
        const doc = iframe.contentDocument || iframe.contentWindow?.document;
        if (doc && doc.body?.innerHTML?.includes('unavailable')) {
          this.contentUnavailable = true;
        }
      } catch {}
    }, 3000);
  }

  setTicketMessage(courseTitle: string) {
    localStorage.setItem('chatbot_prefill', `The content for the course "${courseTitle}" is not visible`);
  }

  getYoutubeEmbed(url: string): string {
    const match = url?.match(/(?:v=|youtu\.be\/)([^&?/]+)/);
    return match ? `https://www.youtube.com/embed/${match[1]}` : '';
  }

  isYoutube(url: string): boolean {
    return url?.includes('youtube.com') || url?.includes('youtu.be');
  }
}
